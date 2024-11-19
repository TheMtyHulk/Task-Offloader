import cv2
from ultralytics import YOLO

model = YOLO('yolov8n.pt') 
def process_video(video_path, output_path):
    # Load the YOLOv8 model
    # Adjust to yolov8m.pt, yolov8l.pt, etc. as needed

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Unable to open video file {video_path}")
        return

    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Create a VideoWriter object to save the output video
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Perform object detection
        results = model(frame)
        
        # Draw bounding boxes and labels on the frame
        for result in results:
            boxes = result.boxes.xyxy
            confidences = result.boxes.conf
            classes = result.boxes.cls
            names = result.names
            
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box)
                confidence = confidences[i]
                cls = int(classes[i])
                label = f'{names[cls]} {confidence:.2f}'
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Write the frame to the output video file
        out.write(frame)

        # Display the frame with detections (optional)
        # cv2.imshow('YOLOv8 Object Detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    # Release the video capture and writer objects
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    
def process_vedio(file_path, new_filename, filename, file_extension, task_id):
    save_dir = 'working_files'
    model = YOLO('yolov8n.pt')
    output_path = f"{save_dir}/{new_filename}{file_extension}"
    process_vedio(file_path, output_path)
    return output_path
