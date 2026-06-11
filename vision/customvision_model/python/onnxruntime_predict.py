import onnxruntime
import numpy as np
from PIL import Image

# Azure Custom Vision General (compact) OD 모델의 표준 앵커 (grid cell 단위)
ANCHORS = np.array([
    [0.573, 0.677],
    [1.87,  2.06 ],
    [3.34,  5.47 ],
    [7.88,  3.52 ],
    [9.77,  9.17 ],
], dtype=np.float32)  # shape: [5, 2] → (width, height)


class ONNXRuntimeObjectDetection:
    def __init__(self, model_filepath, labels):
        opts = onnxruntime.SessionOptions()
        opts.intra_op_num_threads = 1
        self.session = onnxruntime.InferenceSession(
            model_filepath,
            sess_options=opts,
            providers=['CPUExecutionProvider'],
        )
        self.labels = labels
        self.num_classes = len(labels)
        self.num_anchors = len(ANCHORS)

        self.input_name = self.session.get_inputs()[0].name
        _, _, h, w = self.session.get_inputs()[0].shape
        self.input_height = h  # 416
        self.input_width = w   # 416

    def predict_image(self, image, confidence_threshold=0.5, iou_threshold=0.45):
        image_resized = image.resize((self.input_width, self.input_height))
        # 이 모델은 0~255 raw 값을 입력으로 받음 (정규화 불필요)
        input_data = np.array(image_resized, dtype=np.float32)
        input_data = input_data.transpose(2, 0, 1)          # HWC → CHW
        input_data = np.expand_dims(input_data, axis=0)     # [1, 3, 416, 416]

        raw = self.session.run(None, {self.input_name: input_data})[0]
        return self._decode(raw, confidence_threshold, iou_threshold)

    def _sigmoid(self, x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    def _softmax(self, x):
        e = np.exp(x - np.max(x, axis=0, keepdims=True))
        return e / e.sum(axis=0, keepdims=True)

    def _decode(self, output, conf_thresh, iou_thresh):
        # output: [1, 35, 13, 13]  35 = num_anchors*(5+num_classes)
        _, _, grid_h, grid_w = output.shape
        values = 5 + self.num_classes

        # [1, 5, 7, 13, 13]
        out = output.reshape(1, self.num_anchors, values, grid_h, grid_w)[0]

        tx = self._sigmoid(out[:, 0, :, :])   # [A, H, W]
        ty = self._sigmoid(out[:, 1, :, :])
        tw = out[:, 2, :, :]
        th = out[:, 3, :, :]
        conf = self._sigmoid(out[:, 4, :, :])

        # class softmax: [A, C, H, W] → apply per anchor-cell
        cls_raw = out[:, 5:, :, :]            # [A, C, H, W]
        cls_prob = np.zeros_like(cls_raw)
        for a in range(self.num_anchors):
            for gy in range(grid_h):
                for gx in range(grid_w):
                    cls_prob[a, :, gy, gx] = self._softmax(cls_raw[a, :, gy, gx])

        # grid offsets
        grid_x = np.arange(grid_w, dtype=np.float32).reshape(1, 1, grid_w)
        grid_y = np.arange(grid_h, dtype=np.float32).reshape(1, grid_h, 1)

        # 정규화된 bbox 중심 및 크기
        cx = (tx + grid_x) / grid_w
        cy = (ty + grid_y) / grid_h
        bw = ANCHORS[:, 0].reshape(-1, 1, 1) * np.exp(tw) / grid_w
        bh = ANCHORS[:, 1].reshape(-1, 1, 1) * np.exp(th) / grid_h

        best_cls = np.argmax(cls_prob, axis=1)   # [A, H, W]
        best_prob = np.max(cls_prob, axis=1)      # [A, H, W]
        score = conf * best_prob                  # [A, H, W]

        detections = []
        for a in range(self.num_anchors):
            for gy in range(grid_h):
                for gx in range(grid_w):
                    s = float(score[a, gy, gx])
                    if s < conf_thresh:
                        continue
                    left = float(np.clip(cx[a, gy, gx] - bw[a, gy, gx] / 2, 0, 1))
                    top  = float(np.clip(cy[a, gy, gx] - bh[a, gy, gx] / 2, 0, 1))
                    w    = float(np.clip(bw[a, gy, gx], 0, 1))
                    h    = float(np.clip(bh[a, gy, gx], 0, 1))
                    detections.append({
                        "tagName": self.labels[int(best_cls[a, gy, gx])],
                        "probability": s,
                        "boundingBox": {"left": left, "top": top, "width": w, "height": h},
                    })

        return self._nms(detections, iou_thresh)

    def _nms(self, detections, iou_thresh):
        by_class = {}
        for d in detections:
            by_class.setdefault(d["tagName"], []).append(d)

        result = []
        for preds in by_class.values():
            preds.sort(key=lambda x: -x["probability"])
            kept = []
            while preds:
                best = preds.pop(0)
                kept.append(best)
                preds = [p for p in preds if self._iou(best["boundingBox"], p["boundingBox"]) < iou_thresh]
            result.extend(kept)
        return result

    def _iou(self, a, b):
        ax2, ay2 = a["left"] + a["width"], a["top"] + a["height"]
        bx2, by2 = b["left"] + b["width"], b["top"] + b["height"]
        ix1 = max(a["left"], b["left"])
        iy1 = max(a["top"],  b["top"])
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)
        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        union = a["width"] * a["height"] + b["width"] * b["height"] - inter
        return inter / union if union > 0 else 0
