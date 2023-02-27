import numpy as np
import torch
import torchvision.transforms as transforms
import os
import cv2



def from_frames_to_clips(frames, chunk_size, frequency):
    frame_cnt = len(frames)

    # Cut frames
    assert(frame_cnt > chunk_size)

    clipped_length = frame_cnt - chunk_size
    clipped_length = (clipped_length // frequency) * frequency  # The start of last chunk
    frame_indices = [] # Frames to chunks
    for i in range(clipped_length // frequency + 1):
        frame_indices.append([j for j in range(i * frequency, i * frequency + chunk_size)])

    frame_indices = np.array(frame_indices)

    return frame_indices


def split_clip_indices_into_batches(frame_indices, batch_size):
    chunk_num = frame_indices.shape[0]
    batch_num = int(np.ceil(chunk_num / batch_size)) # Chunks to batches
    frame_indices = np.array_split(frame_indices, batch_num, axis=0) # batch_size x (dimensione di clip che fittano in una batch)
    return np.asarray(frame_indices)


# Normalize the video frames with mean and standard deviation calculated across all images
# ResNet50 was pretrained on ImageNet Than trained on Kinetics
def kinetics_mean_std():
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    return mean, std

def load_rgb_batch(frames_dir, rgb_files, frame_indices):
    batch_data = np.zeros(frame_indices.shape + (10, 3, 224, 224))  # B=16 x T=16 x CROP=10 x CH=3 x H=224 x W=224

    mean, std = kinetics_mean_std()
    crop_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(240), # for the UCF-CRIME is 240 else 256
        transforms.TenCrop(224),
        transforms.Lambda(lambda crops: torch.stack([crop_transform(crop) for crop in crops])),
    ])

    # frame_indices.shape[0] = num of batches
    for batch_index in range(frame_indices.shape[0]):

        # frame_indices.shape[1] = num of frames inside a clip
        for frame_index in range(frame_indices.shape[1]):
            # read a single frame
            frame = cv2.imread(os.path.join(frames_dir, rgb_files[frame_indices[batch_index][frame_index]]))

            # apply data augmentation
            frame = transform(frame)

            batch_data[batch_index, frame_index, :, :, :, :] = frame

    return batch_data