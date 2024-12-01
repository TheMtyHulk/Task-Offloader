import imageio
from ultralytics import YOLO
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import cv2
def plot_detections(image, results):
    fig, ax = plt.subplots(1)
    ax.imshow(image)

    # Iterate over the results list
    for result in results:
        boxes = result.boxes
        names = result.names

        # Iterate over the detections
        for i, box in enumerate(boxes.xyxy):
            x1, y1, x2, y2 = box[:4]
            confidence = boxes.conf[i]  # Access the confidence score
            class_id = boxes.cls[i]  # Access the class id
            label = names[int(class_id)]  # Get the label name

            rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=1, edgecolor='r', facecolor='none')
            ax.add_patch(rect)
            plt.text(x1, y1, f'{label} {confidence:.2f}', color='white', fontsize=8, bbox=dict(facecolor='red', alpha=0.5, pad=0.2))

    plt.axis('off')
    return

def process_video(video_path, new_filename, filename, file_extension, task_id):
    # Load the YOLOv8 model
    model = YOLO('yolov8n.pt')  # Adjust to yolov8m.pt, yolov8l.pt, etc. as needed

    # Open the video file
    reader = imageio.get_reader(video_path)
    fps = reader.get_meta_data()['fps']

    # Create a VideoWriter object to save the output video
    save_dir = 'working_files'
    output_path = f"{save_dir}/{new_filename}{file_extension}"
    writer = imageio.get_writer(output_path, fps=fps)

    for frame in reader:
        # Perform object detection
        results = model(frame)

        # Draw bounding boxes and labels on the frame
        for result in results:
            boxes = result.boxes
            names = result.names

            for i, box in enumerate(boxes.xyxy):
                x1, y1, x2, y2 = map(int, box[:4])
                confidence = boxes.conf[i]
                class_id = int(boxes.cls[i])
                label = f"{names[class_id]} {confidence:.2f}"

                frame = cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                frame = cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        writer.append_data(frame)

    reader.close()
    writer.close()
    return output_path

# Example usage
# if __name__ == "__main__":
#     video_output = process_video(r'D:/Task-Offloader/tasks/videos/d.mp4', 'processed_video', 'd', '.mp4', 'task2')
#     print(f"Processed video saved to {video_output}")