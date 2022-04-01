import io
import uvicorn

from common.segment import get_segment, inference
from fastapi import Response, FastAPI, File

model = get_segment()

app = FastAPI()


@app.post("/segment")
def get_segmentation(file: bytes = File(...)):
    segmented_image = inference(model, file)
    bytes_io = io.BytesIO
    segmented_image.save(bytes_io, format="PNG")
    return Response(bytes_io.getvalue(), media_type="image/png")



def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()