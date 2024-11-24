from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def load_image(image_path):
    # Load an image from file
    img = cv2.imread(image_path)
    # Convert the image from BGR to RGB (OpenCV loads images in BGR format)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img_rgb

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
    # plt.show()

def process_img(file_path, new_filename, filename, file_extension, task_id):
    # Load the YOLOv8 model (ensure you have downloaded the model weights)
    model = YOLO('yolov8n.pt')  # Adjust to yolov8m.pt, yolov8l.pt, etc. as needed

    # Load the image
    image = load_image(file_path)
    image_resized = cv2.resize(image, (1000, 650))

    # Perform object detection
    results = model(image_resized)

    # Print results to understand its structure
    # print(results)

    # Plot the detections
    plot_detections(image_resized, results)

    # Draw bounding boxes and labels on the image
    for result in results:
        boxes = result.boxes
        names = result.names

        for i, box in enumerate(boxes.xyxy):
            x1, y1, x2, y2 = box[:4]
            confidence = boxes.conf[i]
            class_id = boxes.cls[i]
            label = names[int(class_id)]

            cv2.rectangle(image_resized, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
            cv2.putText(image_resized, f'{label} {confidence:.2f}', (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

    # Save the processed image
    save_dir = 'working_files'
    output_path = f"{save_dir}/{new_filename}{file_extension}"
    cv2.imwrite(output_path, cv2.cvtColor(image_resized, cv2.COLOR_RGB2BGR))  # Convert back to BGR for saving
    return output_path

# if __name__ == "__main__":
#     image_path = 'OIP.jpg'  # Replace with the path to your image
#     process_img(image_path, 'processed_image', 'OIP', '.jpg', 'task_id')