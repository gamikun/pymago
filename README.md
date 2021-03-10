# Install

```
pip install pymago
```

# Usage

## Convert all files into another format

```
# Take all the png files and convert them into webp
mago convert directory/*.png -format webp
```

## Tint images

```
# Tint all images from the directory with blue color
mago tint path/to/images/*.png -color "blue"
```

## Optimize PNG's

```
# Optimize all png files in the directory by replacing them
mago pngquant *.png
```

## Resize an image given a maximum

```
# Change all images sizes but only when they are greater than 1280
mago resizer *.png -m 1280
```