import imageio
import os
import numpy
filenames = []
for ch in range(1,9):
	filenames.append('Data/10-20-17/ru-x-40.0-50.0-y-0.0-0.5/ch{}.png'.format(ch))
images = []
for filename in filenames:
	images.append(imageio.imread(filename))
imageio.mimsave('Data/10-20-17/movie.gif', images, fps = 2)