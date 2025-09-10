"""
Custom video display widget with ROI selection capability
"""

import cv2
from PyQt5 import QtCore, QtGui, QtWidgets
from typing import Optional, Tuple

class VideoLabel(QtWidgets.QLabel):
    """
    QLabel를 확장하여 프레임을 표시하고 마우스로 ROI를 그릴 수 있도록 함.
    
    표시된 영상은 aspect-fit(KeepAspectRatio)로 축소/확대되므로, 
    위젯 좌표를 원본 프레임 좌표로 정확히 매핑한다.
    """

    roi_changed = QtCore.pyqtSignal(object)  # (x,y,w,h) or None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(QtCore.Qt.AlignCenter)
        # 현대적 비디오 디스플레이 스타일링 with gradient borders
        self.setStyleSheet("""
            VideoLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(43, 43, 43, 0.95), stop:1 rgba(30, 30, 30, 0.9));
                border: 3px solid transparent;
                border-radius: 15px;
                color: #ecf0f1;
                font-size: 15px;
                font-weight: 600;
            }
            VideoLabel:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(102, 126, 234, 0.2), stop:1 rgba(118, 75, 162, 0.2));
                border: 3px solid qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
            }
        """)
        
        # 기본 최소 크기를 늘려 영상이 더 크게 보이도록 함
        self.setMinimumSize(640, 360)
        
        # 위젯이 가능한 공간을 넓게 차지하도록 확장 정책 설정
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, 
            QtWidgets.QSizePolicy.Expanding
        )
        
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
        """QImage를 위젯에 표시"""
        # keep a reference to qimg to avoid underlying buffer being freed
        self._last_qimg = qimg
        
        try:
            print(f"[VideoLabel] 프레임 설정: {qimg.width()}x{qimg.height()}")
        except Exception:
            print("[VideoLabel] 프레임 설정 중 오류")
            
        # store original frame size
        self._orig_size = (qimg.width(), qimg.height())
        pix = QtGui.QPixmap.fromImage(qimg).scaled(
            self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self._disp_size = (pix.width(), pix.height())
        
        # compute offsets to center the pixmap
        left = max(0, (self.width() - self._disp_size[0]) // 2)
        top = max(0, (self.height() - self._disp_size[1]) // 2)
        self._disp_offset = (left, top)
        self.setPixmap(pix)

    def paintEvent(self, ev):
        """ROI 시각화를 위한 커스텀 페인트 이벤트"""
        super().paintEvent(ev)
        
        # persistent ROI 시각화: 직접 그리기
        if self._last_roi is not None and self._orig_size and self._disp_size:
            qp = QtGui.QPainter(self)
            pen = QtGui.QPen(QtGui.QColor(0, 255, 0))
            pen.setWidth(3)
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
                
                # ROI 정보 텍스트 표시
                qp.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
                font = QtGui.QFont()
                font.setPointSize(10)
                qp.setFont(font)
                qp.drawText(dx + 5, dy + 20, f"ROI: {rw}x{rh}")
                
            qp.end()

    def mousePressEvent(self, ev: QtGui.QMouseEvent):
        """마우스 클릭으로 ROI 선택 시작"""
        if ev.button() == QtCore.Qt.LeftButton:
            self._origin = ev.pos()
            self._rubber.setGeometry(QtCore.QRect(self._origin, QtCore.QSize()))
            self._rubber.show()

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent):
        """마우스 드래그로 ROI 영역 조정"""
        if self._origin is not None:
            rect = QtCore.QRect(self._origin, ev.pos()).normalized()
            self._rubber.setGeometry(rect)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent):
        """마우스 릴리즈로 ROI 선택 완료"""
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
        """더블클릭으로 ROI 초기화"""
        self._last_roi = None
        self.roi_changed.emit(None)
        self.update()  # 화면 갱신으로 ROI 표시 제거