
import torch
import cv2
import imageio

# Load the YOLOv5 model
# device = 'cuda' if torch.cuda.is_available() else 'cpu'
# print(device)
model = torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)
# model = torch.hub.load('ultralytics/yolov5', 'yolov5n')

# model = torch.hub.load('ultralytics/yolov5', 'yolov5n')

# Initialize the video capture
cap = cv2.VideoCapture('people.mp4')
if not cap.isOpened():
    print("Error: Could not open the video file.")
    exit()

# Retrieve the frame width, height, and FPS from the input video
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Initialize the writer with imageio, using ffmpeg to write the video
writer = imageio.get_writer('output.mp4', fps=fps, codec='libx264', quality=8)

while True:
    ret, img = cap.read()
    if not ret:
        break

    # Perform object detection
    result = model(img)
    data_frame = result.pandas().xyxy[0]

    # Draw bounding boxes and labels on the image
    for _, row in data_frame.iterrows():
        x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
        label, conf = row['name'], row['confidence']
        text = f"{label} {conf:.2f}"

        cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 0), 2)
        cv2.putText(img, text, (x1, y1 - 5), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 0), 2)

    # Convert the image to RGB before writing to imageio
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    writer.append_data(rgb_img)

    # Optionally show the image
    # cv2.imshow('Processed Frame', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
writer.close()
cv2.destroyAllWindows()
