#!/usr/bin/env python3
"""
한글화된 PyQt5 CCTV 다중 스트림 탐지 PoC

- YOLOv8 모델을 한 번 로드하여 패널 간 공유
- 데모 비디오를 파일 대화상자에서 다중 선택으로 추가
- 패널별 시작/중지, 모두 시작/모두 중지
- ROI(영역) 선택: 마우스로 박스를 그려 해당 영역만 추론

주의: PoC 용도로 간결성과 안정성에 초점을 맞춤
"""

import sys
import os
import time
import math
from pathlib import Path

import cv2
from PyQt5 import QtCore, QtGui, QtWidgets

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

# detect Qt WebEngine availability once
try:
    from PyQt5 import QtWebEngineWidgets as _QWEB, QtWebChannel as _QWC
    WEBENGINE_AVAILABLE = True
    print('[GUI] QtWebEngine available')
except Exception:
    WEBENGINE_AVAILABLE = False
    print('[GUI] QtWebEngine NOT available')

# 간단한 영어->한국어 클래스명 매핑 (필요시 확장하세요)
KOREAN_LABEL_MAP = {
    'car': '자동차',
    'cars': '자동차',
    'truck': '트럭',
    'bus': '버스',
    'motorbike': '오토바이',
    'motorcycle': '오토바이',
    'bike': '오토바이',
    'bicycle': '자전거',
    'person': '사람',
    'people': '사람',
    'van': '밴',
    'work_van': '화물밴',
    'suv': 'SUV',
    'construction_vehicle': '건설차량',
    'caravan': '카라반',
    'trailer': '트레일러',
}

# 차량별 점수(ESALF/점수 기준)
# 사용자 요청: 점수 매핑만 아래 값으로 교체
SCORE_MAP = {
    'bicycle': 0,
    'person': 0,
    'people': 0,
    'car': 1,
    'cars': 1,
    'suv': 1,
    'motorbike': 1,
    'motorcycle': 1,
    'bike': 1,
    'van': 150,
    'work_van': 7950,
    'caravan': 7950,
    'bus': 10430,
    'construction_vehicle': 24820,
    'trailer': 24820,
    'truck': 25160,
}

# 보수 기준 임계값 (누적 ESAL 기준)
# 사용자 제공 표에 따라 누적 ESAL로 보수 단계 구분
# 기존 코드와의 호환성을 위해 (threshold, message) 형태를 유지합니다.
MAINTENANCE_THRESHOLDS = [
    (1_000_000, '전면재포장 (설계 대비 100%, 20년 후)'),
    (850_000, '중간보수 (설계 대비 85%, 17년 후)'),
    (700_000, '표층보수 (설계 대비 70%, 14년 후)'),
    (500_000, '예방보수 (설계 대비 50%, 10년 후)'),
]

# 상세 보수 일정/설계 대비 정보를 기계적으로 사용하기 위한 보조 데이터 구조
MAINTENANCE_SCHEDULE = [
    {
        'stage': '예방보수',
        'cumulative_esal': 500_000,
        'design_pct': 50,
        'timing_years': 10,
        'note': '예방적 유지보수 (균열 실링, 표면 처리)'
    },
    {
        'stage': '표층보수',
        'cumulative_esal': 700_000,
        'design_pct': 70,
        'timing_years': 14,
        'note': '표층 보수 (5cm 절삭 후 재포장)'
    },
    {
        'stage': '중간보수',
        'cumulative_esal': 850_000,
        'design_pct': 85,
        'timing_years': 17,
        'note': '중간층 보수 (10cm 절삭 후 재포장)'
    },
    {
        'stage': '전면재포장',
        'cumulative_esal': 1_000_000,
        'design_pct': 100,
        'timing_years': 20,
        'note': '전면 재포장 (20cm 기층까지 재포장)'
    },
]

# 장기 누적 관리 임계값 (예시)
LONG_TERM = {
    'monthly': 123000,
    'yearly': 1496500,
}

# --- DEBUG: detect any QWidget/QLabel/QRubberBand instantiation before QApplication is created ---
import traceback as _traceback
_orig_qwidget_init = QtWidgets.QWidget.__init__
_orig_qlabel_init = QtWidgets.QLabel.__init__
_orig_rubber_init = QtWidgets.QRubberBand.__init__

def _debug_init_wrapper(orig, name):
    def _wrapped(self, *a, **kw):
        try:
            if QtWidgets.QApplication.instance() is None:
                print(f"[DEBUG] {name}.__init__ called BEFORE QApplication (stack):")
                _traceback.print_stack()
        except Exception:
            pass
        return orig(self, *a, **kw)
    return _wrapped

QtWidgets.QWidget.__init__ = _debug_init_wrapper(_orig_qwidget_init, 'QWidget')
QtWidgets.QLabel.__init__ = _debug_init_wrapper(_orig_qlabel_init, 'QLabel')
QtWidgets.QRubberBand.__init__ = _debug_init_wrapper(_orig_rubber_init, 'QRubberBand')
# --- end debug ---

# NTIS API 키는 기본적으로 환경변수에서 읽되, GUI에서 입력/저장할 수 있도록 합니다.
DEFAULT_NTIS_API_KEY = os.getenv("NTIS_API_KEY")

script_dir = Path(__file__).resolve().parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))
from ntis_client import get_cctv_list


class NtisFetchWorker(QtCore.QThread):
    """NTIS에서 CCTV 목록을 가져오는 비동기 워커"""
    finished = QtCore.pyqtSignal(list)
    error = QtCore.pyqtSignal(str)

    def __init__(self, service_key: str = None, parent=None):
        super().__init__(parent)
        self.service_key = service_key
        self._running = True

    def run(self):
        try:
            lst = get_cctv_list(self.service_key)
            self.finished.emit(lst)
        except Exception as e:
            self.error.emit(str(e))


class StreamWorker(QtCore.QThread):
    """비디오 소스를 읽고 모델 추론을 수행하여 QImage를 방출한다.
    roi 속성이 설정되면 해당 영역만 크롭해서 추론하고, 결과를 원본 프레임에 오버레이한다.
    """

    frame_ready = QtCore.pyqtSignal(object)  # QImage
    status = QtCore.pyqtSignal(str)
    # emits a dict mapping class_name->count
    count_changed = QtCore.pyqtSignal(object)

    def __init__(self, source: str, model=None, model_path: str = None, imgsz: int = 640, conf: float = 0.25):
        super().__init__()
        self.source = source
        self.model = model
        self.model_path = model_path
        self.imgsz = imgsz
        self.conf = conf
        self._running = True

        # ROI: (x, y, w, h) in 원본 프레임 픽셀 좌표 또는 None
        self.roi = None

        # Counting 관련 변수
        self.count = 0
        self.counts = {}  # class_name -> count
        # 트랙 리스트: {'pos': (x,y), 'last_seen': timestamp}
        self.tracks = []
        self.track_ttl = 1.0

    def stop(self):
        self._running = False

    def run(self):
        if YOLO is None and self.model is None and not self.model_path:
            self.status.emit("모델을 찾을 수 없음")
            return

        model = self.model
        if model is None:
            try:
                model = YOLO(self.model_path)
            except Exception as e:
                self.status.emit(f"모델 로드 실패: {e}")
                return

        print(f"[StreamWorker] opening source: {self.source}")
        cap = cv2.VideoCapture(self.source)
        opened = cap.isOpened()
        print(f"[StreamWorker] cap.isOpened={opened}")
        if not opened:
            self.status.emit("소스 열기 실패")
            print(f"[StreamWorker] failed to open source: {self.source}")
            return

        self.status.emit("실행 중")
        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            annotated = frame
            results = None
            try:
                roi = self.roi
                if roi:
                    x, y, w, h = roi
                    h_frame, w_frame = frame.shape[:2]
                    x = max(0, min(int(x), w_frame - 1))
                    y = max(0, min(int(y), h_frame - 1))
                    w = max(1, min(int(w), w_frame - x))
                    h = max(1, min(int(h), h_frame - y))
                    crop = frame[y : y + h, x : x + w]
                    results = model(crop, imgsz=self.imgsz, conf=self.conf)
                    try:
                        annotated_crop = results[0].plot()
                    except Exception:
                        annotated_crop = crop
                    annotated = frame.copy()
                    try:
                        annotated[y : y + h, x : x + w] = annotated_crop
                    except Exception:
                        annotated = frame
                else:
                    results = model(frame, imgsz=self.imgsz, conf=self.conf)
                    annotated = results[0].plot()
            except Exception as e:
                self.status.emit(f"추론 오류: {e}")
                annotated = frame

            # counting: roi가 있을 때만 카운트 로직 실행
            try:
                if self.roi and results is not None:
                    boxes = getattr(results[0], 'boxes', None)
                    names = getattr(results[0], 'names', {})
                    det_centroids = []
                    det_classes = []
                    if boxes is not None and hasattr(boxes, 'xyxy'):
                        try:
                            xyxy = boxes.xyxy
                            dets = xyxy.tolist()
                        except Exception:
                            dets = []
                        cls_list = []
                        if hasattr(boxes, 'cls'):
                            try:
                                cls_list = boxes.cls.tolist()
                            except Exception:
                                cls_list = []

                        for i, b in enumerate(dets):
                            if len(b) < 4:
                                continue
                            x1, y1, x2, y2 = b[0:4]
                            cx = x1 + (x2 - x1) / 2.0
                            cy = y1 + (y2 - y1) / 2.0
                            # map to original frame coords by adding roi offset
                            orig_cx = int(self.roi[0] + cx)
                            orig_cy = int(self.roi[1] + cy)
                            det_centroids.append((orig_cx, orig_cy))
                            cls_idx = None
                            if i < len(cls_list):
                                cls_idx = int(cls_list[i])
                            det_classes.append(cls_idx)

                    now = time.time()
                    # cleanup expired tracks
                    self.tracks = [tr for tr in self.tracks if now - tr['last_seen'] < self.track_ttl]

                    for j, c in enumerate(det_centroids):
                        cx, cy = c
                        cls_idx = det_classes[j] if j < len(det_classes) else None
                        is_vehicle = False
                        try:
                            if cls_idx is not None and names:
                                name = str(names.get(cls_idx, '')).lower()
                                if any(k in name for k in ('car', 'truck', 'bus', 'van', 'motor')):
                                    is_vehicle = True
                        except Exception:
                            is_vehicle = False

                        matched = False
                        match_thresh = 50
                        for tr in self.tracks:
                            dx = tr['pos'][0] - cx
                            dy = tr['pos'][1] - cy
                            dist = math.hypot(dx, dy)
                            if dist < match_thresh:
                                tr['pos'] = (cx, cy)
                                tr['last_seen'] = now
                                matched = True
                                break

                        if not matched:
                            self.tracks.append({'pos': (cx, cy), 'last_seen': now})
                            # determine class name
                            cls_name = 'unknown'
                            try:
                                if cls_idx is not None and names:
                                    cls_name = str(names.get(cls_idx, 'unknown'))
                            except Exception:
                                cls_name = 'unknown'
                            # increment per-class and total
                            try:
                                self.counts[cls_name] = self.counts.get(cls_name, 0) + 1
                            except Exception:
                                self.counts = {cls_name: 1}
                            self.count += 1
                            # emit a copy of counts to avoid threading issues
                            try:
                                self.count_changed.emit(dict(self.counts))
                            except Exception:
                                pass

                    # also update status with total count
                    self.status.emit(f"실행 중 | 카운트: {self.count}")
            except Exception:
                pass

            try:
                rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                bytes_per_line = rgb.strides[0]
                qimg = QtGui.QImage(rgb.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
                # ensure QImage owns its buffer (avoid referencing temporary numpy memory)
                qimg = qimg.copy()
                print(f"[StreamWorker] emitting QImage {w}x{h} format=RGB888 bytes_per_line={bytes_per_line} (copied)")
                self.frame_ready.emit(qimg)
            except Exception:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                h, w = gray.shape
                qimg = QtGui.QImage(gray.data, w, h, w, QtGui.QImage.Format_Grayscale8)
                qimg = qimg.copy()
                print(f"[StreamWorker] emitting grayscale QImage {w}x{h} format=Grayscale8 (copied)")
                self.frame_ready.emit(qimg)

        cap.release()
        self.status.emit("중지됨")


class VideoLabel(QtWidgets.QLabel):
    """QLabel를 확장하여 프레임을 표시하고 마우스로 ROI를 그릴 수 있도록 함.

    표시된 영상은 aspect-fit(KeepAspectRatio)로 축소/확대되므로, 위젯 좌표를 원본 프레임 좌표로 정확히 매핑한다.
    """

    roi_changed = QtCore.pyqtSignal(object)  # (x,y,w,h) or None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet("background: black;")
        # 기본 최소 크기를 늘려 영상이 더 크게 보이도록 함
        self.setMinimumSize(640, 360)
        # 위젯이 가능한 공간을 넓게 차지하도록 확장 정책 설정
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._rubber = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self._origin = None
        # 원본 프레임 사이즈 (width, height)
        self._orig_size = None
        # 현재 표시된 pixmap 크기 (width, height) - aspect-fit 후 크기
        self._disp_size = None
        # offset within widget where pixmap is drawn (left, top)
        self._disp_offset = (0, 0)
        # 마지막으로 설정된 roi (원본 이미지 좌표)
        self._last_roi = None

    def set_qimage(self, qimg: QtGui.QImage):
        # keep a reference to qimg to avoid underlying buffer being freed
        self._last_qimg = qimg
        try:
            print(f"[VideoLabel] set_qimage called: qimg size={qimg.width()}x{qimg.height()} format={qimg.format()} widget={self.width()}x{self.height()}")
        except Exception:
            print("[VideoLabel] set_qimage called: (error printing qimg info)")
        # store original frame size
        self._orig_size = (qimg.width(), qimg.height())
        pix = QtGui.QPixmap.fromImage(qimg).scaled(self.size(), QtCore.Qt.KeepAspectRatio)
        self._disp_size = (pix.width(), pix.height())
        # compute offsets to center the pixmap
        left = max(0, (self.width() - self._disp_size[0]) // 2)
        top = max(0, (self.height() - self._disp_size[1]) // 2)
        self._disp_offset = (left, top)
        self.setPixmap(pix)

    def paintEvent(self, ev):
        super().paintEvent(ev)
        # persistent ROI 시각화: 직접 그리기
        if self._last_roi is not None and self._orig_size and self._disp_size:
            qp = QtGui.QPainter(self)
            pen = QtGui.QPen(QtGui.QColor(0, 255, 0))
            pen.setWidth(2)
            qp.setPen(pen)
            ox, oy = self._disp_offset
            dw, dh = self._disp_size
            ow, oh = self._orig_size
            if dw and ow:
                sx = dw / ow
                sy = dh / oh
                rx, ry, rw, rh = self._last_roi
                # roi is in original coords -> map to display coords
                dx = int(rx * sx) + ox
                dy = int(ry * sy) + oy
                dwid = int(rw * sx)
                dhgt = int(rh * sy)
                qp.drawRect(dx, dy, dwid, dhgt)
            qp.end()

    def mousePressEvent(self, ev: QtGui.QMouseEvent):
        if ev.button() == QtCore.Qt.LeftButton:
            self._origin = ev.pos()
            self._rubber.setGeometry(QtCore.QRect(self._origin, QtCore.QSize()))
            self._rubber.show()

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent):
        if self._origin is not None:
            rect = QtCore.QRect(self._origin, ev.pos()).normalized()
            self._rubber.setGeometry(rect)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent):
        if self._origin is None:
            return
        rect = self._rubber.geometry()
        self._rubber.hide()
        self._origin = None

        if self._orig_size is None or self._disp_size is None:
            self._last_roi = None
            self.roi_changed.emit(None)
            return

        ox, oy = self._disp_offset
        dw, dh = self._disp_size
        ow, oh = self._orig_size

        # widget-space rect -> pixmap-space rect (subtract offset)
        x1 = rect.left() - ox
        y1 = rect.top() - oy
        x2 = rect.right() - ox
        y2 = rect.bottom() - oy

        # clamp inside displayed pixmap
        x1 = max(0, min(x1, dw - 1))
        y1 = max(0, min(y1, dh - 1))
        x2 = max(0, min(x2, dw - 1))
        y2 = max(0, min(y2, dh - 1))

        if x2 <= x1 or y2 <= y1:
            self._last_roi = None
            self.roi_changed.emit(None)
            return

        # scale factor from displayed pixmap to original image
        sx = ow / dw
        sy = oh / dh

        rx = int(x1 * sx)
        ry = int(y1 * sy)
        rw = int((x2 - x1) * sx)
        rh = int((y2 - y1) * sy)

        if rw <= 0 or rh <= 0:
            self._last_roi = None
            self.roi_changed.emit(None)
        else:
            self._last_roi = (rx, ry, rw, rh)
            self.roi_changed.emit((rx, ry, rw, rh))

    def mouseDoubleClickEvent(self, ev: QtGui.QMouseEvent):
        # 더블클릭으로 ROI 초기화
        self._last_roi = None
        self.roi_changed.emit(None)


class StreamPanel(QtWidgets.QWidget):
    def __init__(self, source: str, model_path: str):
        super().__init__()
        # basic properties
        self.source = source
        self.model_path = model_path
        self.roi = None
        self.worker = None
        self.model = None
        self.imgsz = 640
        self.conf = 0.25

        # layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(6)
        self.setLayout(self.layout)

        # title
        self.label = QtWidgets.QLabel(source)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.label)

        # video area
        self.video = VideoLabel()
        self.video.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.layout.addWidget(self.video)

        # controls
        btn_layout = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("시작")
        self.stop_btn = QtWidgets.QPushButton("중지")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        self.layout.addLayout(btn_layout)

        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)

        # counter UI
        counter_layout = QtWidgets.QHBoxLayout()
        self.count_label = QtWidgets.QLabel("카운트: 0")
        self.reset_btn = QtWidgets.QPushButton("리셋")
        self.count_chk = QtWidgets.QCheckBox("카운트 활성화")
        self.count_chk.setChecked(True)
        counter_layout.addWidget(self.count_label)
        counter_layout.addWidget(self.reset_btn)
        counter_layout.addWidget(self.count_chk)
        self.layout.addLayout(counter_layout)

        self.reset_btn.clicked.connect(self.reset_count)

        # breakdown
        self.breakdown_label = QtWidgets.QLabel("")
        self.breakdown_label.setWordWrap(True)
        self.layout.addWidget(self.breakdown_label)

        # score display (총합 및 권고)
        self.score_label = QtWidgets.QLabel("")
        self.score_label.setWordWrap(True)
        self.layout.addWidget(self.score_label)

        # connect video ROI signal
        self.video.roi_changed.connect(self.on_roi_changed)

    def on_roi_changed(self, roi):
        self.roi = roi
        if self.worker is not None:
            try:
                self.worker.roi = roi
            except Exception:
                pass

    def start(self):
        if self.worker is not None and self.worker.isRunning():
            return
        if self.model is not None:
            self.worker = StreamWorker(self.source, model=self.model, imgsz=self.imgsz, conf=self.conf)
        else:
            self.worker = StreamWorker(self.source, model_path=self.model_path, imgsz=self.imgsz, conf=self.conf)
        self.worker.frame_ready.connect(self.on_frame)
        self.worker.status.connect(self.on_status)
        try:
            self.worker.count_changed.connect(self.on_count_changed)
        except Exception:
            pass
        if self.roi is not None:
            self.worker.roi = self.roi
        self.worker.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(2000)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def on_frame(self, qimg: QtGui.QImage):
        try:
            self.video.set_qimage(qimg)
            ow, oh = self.video._orig_size if self.video._orig_size else (0, 0)
            self.label.setText(f"{self.source} | 프레임 {ow}x{oh}")
        except Exception as e:
            print(f"[StreamPanel] on_frame error: {e}")

    def on_status(self, msg: str):
        self.label.setText(f"{self.source} | {msg}")

    def on_count_changed(self, counts: object):
        try:
            if not getattr(self, 'count_chk', None) or not self.count_chk.isChecked():
                return
            if not isinstance(counts, dict):
                total = int(counts) if counts is not None else 0
                self.count_label.setText(f"카운트: {total}")
                return
            # 기존 총 카운트 표시
            total = sum(counts.values())
            self.count_label.setText(f"카운트: {total}")

            # SCORE_MAP에 따라 클래스별 소계(subtotal)와 총점(total_score) 계산
            total_score = 0.0
            breakdown_parts = []
            per_class_details = []
            for k, v in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
                name = str(k).lower()
                # find matching score key
                score_per = SCORE_MAP.get(name)
                if score_per is None:
                    for key_candidate in SCORE_MAP.keys():
                        if key_candidate in name:
                            score_per = SCORE_MAP.get(key_candidate)
                            break
                if score_per is None:
                    score_per = 0.0

                class_count = int(v)
                subtotal = class_count * float(score_per)
                total_score += subtotal

                # human readable label (KOREAN_LABEL_MAP may map english keys)
                human = KOREAN_LABEL_MAP.get(name, name)
                per_class_details.append((human, name, class_count, score_per, subtotal))
                breakdown_parts.append(f"{human}({name}): {class_count} × {score_per} = {subtotal:.1f}")

            # determine maintenance recommendation based on total_score
            rec = None
            for thresh, msg in sorted(MAINTENANCE_THRESHOLDS, key=lambda x: -x[0]):
                if total_score >= thresh:
                    rec = msg
                    break
            if rec is None:
                rec = '정기 모니터링' if total_score > 0 else '조치 불필요'

            # 표시: breakdown_label에는 각 클래스 소계, score_label에는 총합 및 권고
            self.breakdown_label.setText('\n'.join(breakdown_parts))
            try:
                self.score_label.setText(f"총점: {total_score:.1f} | 권고: {rec}")
            except Exception:
                pass
        except Exception:
            pass

    def reset_count(self):
        try:
            if self.worker is not None:
                self.worker.count = 0
                try:
                    self.worker.counts = {}
                except Exception:
                    pass
                try:
                    self.worker.count_changed.emit({})
                except Exception:
                    pass
            else:
                if hasattr(self, 'count_label'):
                    self.count_label.setText('카운트: 0')
                    if hasattr(self, 'breakdown_label'):
                        self.breakdown_label.setText('')
        except Exception as e:
            print(f"[StreamPanel] reset_count error: {e}")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, model_path: str = "weights/best.pt"):
        super().__init__()
        self.setWindowTitle("CCTV 다중 스트림 탐지 (PoC)")
        self.model_path = model_path
        self.ntis_api_key = DEFAULT_NTIS_API_KEY

        # central widget + layout
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout()
        central.setLayout(layout)

        # top controls (stream input + buttons)
        control_layout = QtWidgets.QHBoxLayout()
        self.input_line = QtWidgets.QLineEdit()
        self.input_line.setPlaceholderText("rtsp://... 또는 /path/to/video.mp4")
        self.add_btn = QtWidgets.QPushButton("스트림 추가")
        self.add_demo_btn = QtWidgets.QPushButton("데모 비디오 추가")
        self.ntis_btn = QtWidgets.QPushButton("NTIS 카메라 불러오기")
        self.start_all_btn = QtWidgets.QPushButton("모두 시작")
        self.stop_all_btn = QtWidgets.QPushButton("모두 중지")
        control_layout.addWidget(self.input_line)
        control_layout.addWidget(self.add_btn)
        control_layout.addWidget(self.add_demo_btn)
        control_layout.addWidget(self.ntis_btn)
        control_layout.addWidget(self.start_all_btn)
        control_layout.addWidget(self.stop_all_btn)
        layout.addLayout(control_layout)

        # settings row
        settings_layout = QtWidgets.QHBoxLayout()
        self.imgsz_spin = QtWidgets.QSpinBox()
        self.imgsz_spin.setRange(128, 2048)
        self.imgsz_spin.setValue(640)
        self.conf_spin = QtWidgets.QDoubleSpinBox()
        self.conf_spin.setRange(0.01, 1.0)
        self.conf_spin.setSingleStep(0.01)
        self.conf_spin.setValue(0.25)
        settings_layout.addWidget(QtWidgets.QLabel("이미지 크기"))
        settings_layout.addWidget(self.imgsz_spin)
        settings_layout.addWidget(QtWidgets.QLabel("신뢰도"))
        settings_layout.addWidget(self.conf_spin)
        layout.addLayout(settings_layout)

        # 모델 선택/로드 UI
        model_layout = QtWidgets.QHBoxLayout()
        model_label = QtWidgets.QLabel("모델")
        candidate = Path("prog") / "weights" / "best.pt"
        if candidate.exists():
            default_model = str(candidate)
        else:
            default_model = str(Path(self.model_path)) if self.model_path else "weights/best.pt"
        self.model_line = QtWidgets.QLineEdit(default_model)
        self.model_browse = QtWidgets.QPushButton("모델 선택")
        self.model_load = QtWidgets.QPushButton("모델 로드")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_line)
        model_layout.addWidget(self.model_browse)
        model_layout.addWidget(self.model_load)
        layout.addLayout(model_layout)

        # connect model UI actions
        self.model_browse.clicked.connect(self.select_model_file)
        self.model_load.clicked.connect(self.load_model)

        # panels area
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.panels_widget = QtWidgets.QWidget()
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(12)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.panels_widget.setLayout(self.grid)
        self.scroll.setWidget(self.panels_widget)
        layout.addWidget(self.scroll)

        # connect other buttons
        self.add_btn.clicked.connect(self.add_stream_from_input)
        self.add_demo_btn.clicked.connect(self.select_demo_and_add)
        self.ntis_btn.clicked.connect(self.on_ntis)
        self.start_all_btn.clicked.connect(self.start_all)
        self.stop_all_btn.clicked.connect(self.stop_all)

        # model instance (load if default exists)
        self.model = None
        try:
            maybe_path = Path(self.model_line.text().strip())
            if maybe_path.exists() and YOLO is not None:
                try:
                    print(f"[GUI] 자동 모델 로드 시도 {maybe_path}")
                    self.model = YOLO(str(maybe_path))
                    self.model_path = str(maybe_path)
                    print(f"[GUI] 모델 로드 완료: {self.model_path}")
                except Exception as e:
                    print(f"경고: 자동 모델 로드 실패: {e}")
        except Exception:
            pass

        self.panels = []
        self._cols = 1

    def select_model_file(self):
        # 파일 대화상자로 모델 파일을 선택하여 경로 입력란에 채웁니다.
        start_dir = str(Path("prog") / "weights") if (Path("prog") / "weights").exists() else str(Path.cwd())
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, "모델 파일 선택", start_dir, "PyTorch model (*.pt *.pth);;All files (*)")
        if p:
            self.model_line.setText(p)

    def load_model(self):
        path = self.model_line.text().strip()
        if not path:
            QtWidgets.QMessageBox.warning(self, "모델 로드", "모델 경로를 입력하세요")
            return
        p = Path(path)
        if not p.exists():
            QtWidgets.QMessageBox.warning(self, "모델 로드", f"경로를 찾을 수 없습니다: {path}")
            return
        if YOLO is None:
            QtWidgets.QMessageBox.warning(self, "모델 로드", "ultralytics YOLO가 설치되어 있지 않아 모델을 로드할 수 없습니다.")
            return
        try:
            print(f"[GUI] 모델 로드 시도: {path}")
            self.model = YOLO(str(p))
            self.model_path = str(p)
            QtWidgets.QMessageBox.information(self, "모델 로드", f"모델 로드 완료: {path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "모델 로드 실패", f"모델을 불러오는 중 오류 발생: {e}")

    def add_stream_from_input(self):
        src = self.input_line.text().strip()
        if not src:
            return
        self.add_stream(src)
        self.input_line.clear()

    def add_stream(self, source: str):
        panel = StreamPanel(source, self.model_path)
        if self.model is not None:
            panel.model = self.model
        idx = len(self.panels)
        row = idx // self._cols
        col = idx % self._cols
        self.grid.addWidget(panel, row, col)
        self.panels.append(panel)

    def add_demo_videos(self):
        demo_dir = Path("prog") / "demo_videos"
        if not demo_dir.exists():
            return
        for p in sorted(demo_dir.iterdir()):
            if p.suffix.lower() in (".mp4", ".mov", ".avi", ".mkv"):
                self.add_stream(str(p))

    def select_demo_and_add(self):
        demo_dir = Path("prog") / "demo_videos"
        start_dir = str(demo_dir) if demo_dir.exists() else str(Path.cwd())
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "데모 비디오 선택",
                                                          start_dir,
                                                          "비디오 파일 (*.mp4 *.mov *.avi *.mkv);;모든 파일 (*)")
        for f in files:
            self.add_stream(f)

    def _maybe_ask_for_ntis_key(self):
        """키가 없거나 변경하려면 GUI로 입력을 받는다. 저장 옵션도 제공."""
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("NTIS API 키 입력")
        form = QtWidgets.QFormLayout(dlg)
        key_edit = QtWidgets.QLineEdit(dlg)
        if self.ntis_api_key:
            key_edit.setText(self.ntis_api_key)
        key_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
        save_chk = QtWidgets.QCheckBox("영구 저장 (~/.zshrc에 추가)")
        form.addRow("NTIS API Key:", key_edit)
        form.addRow(save_chk)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return False

        v = key_edit.text().strip()
        # sanitize: keep only first line in case user pasted terminal output
        if '\n' in v:
            v = v.splitlines()[0].strip()
        if not v:
            QtWidgets.QMessageBox.warning(self, "입력 오류", "유효한 NTIS API 키를 입력하세요.")
            return False
        # basic validation: common NTIS keys are hex-like; require 16-64 alnum/hex chars
        import re
        if not re.match(r'^[A-Fa-f0-9]{16,64}$', v):
            # warn but allow user to accept non-standard keys
            res = QtWidgets.QMessageBox.question(self, '키 형식 경고',
                '입력한 키가 예상 형식(16-64자리 16진수)과 다릅니다. 계속 저장하시겠습니까?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if res != QtWidgets.QMessageBox.Yes:
                return False

        self.ntis_api_key = v
        if save_chk.isChecked():
            # 시도해 저장 (사용자 홈의 .zshrc 수정)
            try:
                zshrc = os.path.expanduser('~/.zshrc')
                line = f"export NTIS_API_KEY='{self.ntis_api_key}'\n"
                if os.path.exists(zshrc):
                    with open(zshrc, 'r', encoding='utf-8') as f:
                        txt = f.read()
                    if 'export NTIS_API_KEY=' in txt:
                        # 치환
                        import re
                        new_txt = re.sub(r"^export NTIS_API_KEY=.*$", line, txt, flags=re.M)
                        with open(zshrc + '.bak', 'w', encoding='utf-8') as b:
                            b.write(txt)
                        with open(zshrc, 'w', encoding='utf-8') as f:
                            f.write(new_txt)
                    else:
                        with open(zshrc, 'a', encoding='utf-8') as f:
                            f.write('\n' + line)
                else:
                    # 파일이 없으면 새로 생성
                    with open(zshrc, 'w', encoding='utf-8') as f:
                        f.write(line)
                QtWidgets.QMessageBox.information(self, '저장됨', f'키를 {zshrc}에 저장했습니다. 새 터미널에서 자동으로 적용됩니다.')
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, '저장 실패', f'~/.zshrc에 저장하는 동안 오류가 발생했습니다: {e}')

        return True


    def on_ntis(self):
        # NTIS API 키 유무 확인 및 GUI 입력 허용
        if not self.ntis_api_key:
            ok = self._maybe_ask_for_ntis_key()
            if not ok:
                return

        # 간단한 파라미터 입력 다이얼로그
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("NTIS 검색 파라미터")
        form = QtWidgets.QFormLayout(dlg)
        type_edit = QtWidgets.QLineEdit(dlg)
        type_edit.setPlaceholderText("도로 유형 (예: 고속도로, its)")
        cctvtype_spin = QtWidgets.QSpinBox(dlg)
        cctvtype_spin.setRange(1, 5)
        minx = QtWidgets.QLineEdit(dlg)
        maxx = QtWidgets.QLineEdit(dlg)
        miny = QtWidgets.QLineEdit(dlg)
        maxy = QtWidgets.QLineEdit(dlg)
        gettype = QtWidgets.QComboBox(dlg)
        gettype.addItems(["json", "xml"])
        form.addRow("도로 유형(type)", type_edit)
        form.addRow("CCTV 유형(cctvType)", cctvtype_spin)
        form.addRow("minX (경도)", minx)
        form.addRow("maxX (경도)", maxx)
        form.addRow("minY (위도)", miny)
        form.addRow("maxY (위도)", maxy)
        form.addRow("getType", gettype)

        map_btn = QtWidgets.QPushButton("지도에서 선택")
        form.addRow(map_btn)
        # quick presets so map is optional
        preset_layout = QtWidgets.QHBoxLayout()
        preset_btn1 = QtWidgets.QPushButton("성남 (샘플)")
        preset_btn2 = QtWidgets.QPushButton("서울 중심")
        preset_layout.addWidget(preset_btn1)
        preset_layout.addWidget(preset_btn2)
        form.addRow(preset_layout)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)

        # 지도 선택 버튼 동작: QWebEngineView로 map_picker.html 열기
        def open_map_picker():
            try:
                from PyQt5 import QtWebEngineWidgets, QtWebChannel
            except Exception:
                QtWidgets.QMessageBox.warning(self, "환경 문제", "QtWebEngine이 설치되어 있지 않아 지도 기능을 사용할 수 없습니다.")
                return

            map_dlg = QtWidgets.QDialog(self)
            map_dlg.setWindowTitle("지도에서 영역 선택")
            layout_map = QtWidgets.QVBoxLayout(map_dlg)
            view = QtWebEngineWidgets.QWebEngineView()
            layout_map.addWidget(view)

            # bridge object
            class Bridge(QtCore.QObject):
                @QtCore.pyqtSlot(str)
                def sendBbox(self, json_str):
                    import json
                    try:
                        data = json.loads(json_str)
                        # note: use the QLineEdit variables defined above (minx, maxx, miny, maxy)
                        minx.setText(str(data.get('minX')))
                        maxx.setText(str(data.get('maxX')))
                        miny.setText(str(data.get('minY')))
                        maxy.setText(str(data.get('maxY')))
                        # close dialog after selection
                        QtCore.QMetaObject.invokeMethod(map_dlg, 'accept', QtCore.Qt.QueuedConnection)
                    except Exception as e:
                        print('map bridge error', e)

            channel = QtWebChannel.QWebChannel()
            bridge = Bridge()
            channel.registerObject('bridge', bridge)
            view.page().setWebChannel(channel)

            file_path = str(Path(script_dir) / 'map_picker.html')
            view.load(QtCore.QUrl.fromLocalFile(file_path))
            map_dlg.resize(800, 600)
            map_dlg.exec_()

        map_btn.clicked.connect(open_map_picker)
        # preset handlers
        def _preset_seongnam():
            minx.setText('127.12')
            maxx.setText('127.13')
            miny.setText('37.42')
            maxy.setText('37.44')

        def _preset_seoul():
            minx.setText('126.90')
            maxx.setText('127.20')
            miny.setText('37.40')
            maxy.setText('37.60')

        preset_btn1.clicked.connect(_preset_seongnam)
        preset_btn2.clicked.connect(_preset_seoul)

        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return

        params = {}
        if type_edit.text().strip():
            params['type'] = type_edit.text().strip()
        params['cctvType'] = int(cctvtype_spin.value())
        try:
            params['minX'] = float(minx.text()) if minx.text().strip() else None
            params['maxX'] = float(maxx.text()) if maxx.text().strip() else None
            params['minY'] = float(miny.text()) if miny.text().strip() else None
            params['maxY'] = float(maxy.text()) if maxy.text().strip() else None
        except Exception:
            QtWidgets.QMessageBox.warning(self, "입력 오류", "좌표 입력을 확인하세요")
            return
        params['getType'] = gettype.currentText()

        self.ntis_btn.setEnabled(False)
        # run worker manually and use get_cctv_list with params on GUI side
        def _run_and_emit():
            try:
                print(f"[NTIS] 호출 파라미터: getType={params.get('getType')} cctvType={params.get('cctvType')} bbox=({params.get('minX')},{params.get('minY')})-({params.get('maxX')},{params.get('maxY')}) key_present={bool(self.ntis_api_key)})")
                items = get_cctv_list(service_key=self.ntis_api_key, **params)
                print(f"[NTIS] 응답 항목 수: {len(items) if items is not None else 'None'}")
                # call back into GUI thread
                QtCore.QTimer.singleShot(0, lambda: self.on_ntis_result(items))
            except Exception as e:
                print(f"[NTIS] 오류: {e}")
                QtCore.QTimer.singleShot(0, lambda: self.on_ntis_error(str(e)))
            finally:
                # re-enable button in the GUI thread
                QtCore.QTimer.singleShot(0, lambda: self.ntis_btn.setEnabled(True))

        # execute in background thread to avoid blocking GUI (use threading.Thread for simplicity)
        import threading
        t = threading.Thread(target=_run_and_emit, daemon=True)
        t.start()

    def on_ntis_error(self, msg: str):
        self.ntis_btn.setEnabled(True)
        QtWidgets.QMessageBox.critical(self, "NTIS 오류", f"목록을 불러오는 중 오류가 발생했습니다:\n{msg}")

    def on_ntis_result(self, items: list):
        self.ntis_btn.setEnabled(True)
        if not items:
            QtWidgets.QMessageBox.information(self, "NTIS", "카메라 목록이 비어있습니다.")
            return

        # 간단한 선택 다이얼로그
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("NTIS 카메라 선택")
        layout = QtWidgets.QVBoxLayout(dlg)
        listw = QtWidgets.QListWidget()
        for it in items:
            name = it.get('name') or it.get('id') or ''
            stream = it.get('stream_url') or ''
            lw_item = QtWidgets.QListWidgetItem(f"{name} - {stream}")
            lw_item.setData(QtCore.Qt.UserRole, stream)
            listw.addItem(lw_item)
        layout.addWidget(listw)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            sel = listw.currentItem()
            if sel:
                stream = sel.data(QtCore.Qt.UserRole)
                if stream:
                    self.add_stream(stream)

    def start_all(self):
        for p in self.panels:
            p.model_path = self.model_path
            p.model = getattr(self, "model", None)
            p.imgsz = int(self.imgsz_spin.value())
            p.conf = float(self.conf_spin.value())
            p.start()

    def stop_all(self):
        for p in self.panels:
            p.stop()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        for p in self.panels:
            p.stop()
        super().closeEvent(event)


def main():
    print("[GUI] 시작")
    app = QtWidgets.QApplication(sys.argv)
    model_path = "weights/best.pt"
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    w = MainWindow(model_path)
    w.resize(1100, 700)
    print("[GUI] 창 표시")
    w.show()
    print("[GUI] 이벤트 루프 진입")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

