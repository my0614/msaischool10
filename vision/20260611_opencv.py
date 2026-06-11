import os
import gradio as gr
import cv2


DEFAULT_SCALE_FACTOR = 1.1
DEFAULT_MIN_NEIGHBORS = 5
DEFAULT_MIN_SIZE = 30

haarcascade_features = [
    "haarcascade_frontalface_default.xml",
    "haarcascade_frontalface_alt.xml",
    "haarcascade_frontalface_alt2.xml",
    "haarcascade_eye.xml",
    "haarcascade_smile.xml",
    "haarcascade_fullbody.xml",
    "haarcascade_upperbody.xml",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def detect_object(image_array, scale_factor, min_neighbors, min_size, cascade, is_bgr=True):
    image_array = image_array.copy()

    cascade_file_path = cv2.data.haarcascades + cascade
    model = cv2.CascadeClassifier(cascade_file_path)

    bounding_boxes = model.detectMultiScale(
        image=image_array,
        scaleFactor=float(scale_factor),
        minNeighbors=int(min_neighbors),
        minSize=(int(min_size), int(min_size)),
    )

    for x, y, w, h in bounding_boxes:
        cv2.rectangle(image_array, (x, y), (x + w, y + h), (0, 255, 0), 2)

    if is_bgr:
        image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)

    return image_array


# 정적 이미지 저장 (파일이 있을 때만 실행)
static_image_path = os.path.join(SCRIPT_DIR, "istockphoto-1480574526-2048x2048.jpg")
if os.path.exists(static_image_path):
    image = cv2.imread(static_image_path)
    result = detect_object(
        image,
        scale_factor=DEFAULT_SCALE_FACTOR,
        min_neighbors=DEFAULT_MIN_NEIGHBORS,
        min_size=DEFAULT_MIN_SIZE,
        cascade="haarcascade_frontalface_default.xml",
    )
    output_path = os.path.join(SCRIPT_DIR, "result_20260611_opencv.jpg")
    result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, result_bgr)
    print(f"결과 이미지 저장 완료: {output_path}")


with gr.Blocks() as demo:

    scale_factor_state  = gr.State(DEFAULT_SCALE_FACTOR)
    min_neighbors_state = gr.State(DEFAULT_MIN_NEIGHBORS)
    min_size_state      = gr.State(DEFAULT_MIN_SIZE)
    cascade_state       = gr.State("haarcascade_frontalface_default.xml")

    def stream_webcam(image_array, scale_factor, min_neighbors, min_size, cascade):
        result_image = detect_object(
            image_array, scale_factor, min_neighbors, min_size, cascade,
            is_bgr=False,
        )
        return result_image

    def click_apply(scale_factor, min_neighbors, min_size, cascade):
        return scale_factor, min_neighbors, min_size, cascade

    def change_haarcascade(cascade):
        print(cascade)

    gr.Markdown("객체 감지 서비스")

    haarcascade_dropdown = gr.Dropdown(
        label="감지 유형 선택",
        choices=haarcascade_features,
        interactive=True,
        value="haarcascade_frontalface_default.xml",
    )

    with gr.Row():
        scale_factor_number = gr.Number(
            label="scaleFactor", value=DEFAULT_SCALE_FACTOR, interactive=True
        )
        min_neighbor_number = gr.Number(
            label="minNeighbors", value=DEFAULT_MIN_NEIGHBORS, interactive=True, precision=0
        )
        min_size_number = gr.Number(
            label="minSize (px)", value=DEFAULT_MIN_SIZE, interactive=True, precision=0
        )

    apply_button = gr.Button("적용")

    with gr.Row():
        stream_image = gr.Image(
            label="웹캠",
            sources=["webcam"],
            webcam_options=gr.WebcamOptions(mirror=False),
        )
        result_image = gr.Image(label="감지 결과", interactive=False)

    stream_image.stream(
        stream_webcam,
        inputs=[stream_image, scale_factor_state, min_neighbors_state, min_size_state, cascade_state],
        outputs=[result_image],
    )

    apply_button.click(
        click_apply,
        inputs=[scale_factor_number, min_neighbor_number, min_size_number, haarcascade_dropdown],
        outputs=[scale_factor_state, min_neighbors_state, min_size_state, cascade_state],
    )

    haarcascade_dropdown.change(change_haarcascade, inputs=[haarcascade_dropdown])

demo.launch()
