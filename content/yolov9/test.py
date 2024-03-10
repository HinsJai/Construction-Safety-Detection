from ultralytics import YOLO


def train_model():

    model.train(
        data="./data.yaml",
        epochs=1,
        imgsz=640,
        batch=32,
        workers=2,
        name="epochs_100",
        patience=10,  # early stopping patience
        save=True,
        optimizer="AdamW",
        verbose=True,
        plots=True,
    )


if __name__ == "__main__":
    model = YOLO("yolov9c.pt")
    train_model()
