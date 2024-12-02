# What is this

Field Merger is a simple GUI tool that merges two field images using vertical and horizontal shifts. Additionally, it can perform deinterlacing using FFmpeg.

## Features

- Merge two selected field images
- Adjust vertical and horizontal shifts
- Zoom in and out using the mouse wheel
- Save the merged image and perform deinterlacing

## Prerequisites

- Docker Compose

## Target

- WSL2 on Windows

For other platforms, modify the following sections as needed:
```
      - /mnt/c/Users:/mnt/windows
```

```
        file_path = filedialog.askopenfilename(initialdir="/mnt/windows")
```

## How to start
```
docker-compose build
docker-compose up
```
