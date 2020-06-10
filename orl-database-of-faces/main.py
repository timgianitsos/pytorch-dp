import os
from os.path import join, dirname
import random

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from matplotlib import pyplot as plt
from tqdm import trange

def read_pgm(pgmf):
	"""Return a raster of integers from a PGM as a list of lists."""
	#https://stackoverflow.com/a/35726744/7102572
	assert pgmf.readline().decode('utf-8') == 'P5\n'
	(width, height) = [int(i) for i in pgmf.readline().split()]
	depth = int(pgmf.readline())
	assert depth <= 255

	raster = []
	for y in range(height):
		row = []
		for y in range(width):
			row.append(ord(pgmf.read(1)))
		raster.append(row)
	return torch.tensor(raster, dtype=torch.uint8)

def display_example():
	plt.imshow(read_pgm(open(join(dirname(__file__), 's1', '1.pgm'), 'rb')), plt.cm.gray)
	plt.show()

def get_data():
	train_features = torch.empty(size=(280, 1, 112, 92), dtype=torch.uint8)
	train_labels = torch.empty(size=(280,), dtype=torch.uint8)
	test_features = torch.empty(size=(120, 1, 112, 92), dtype=torch.uint8)
	test_labels = torch.empty(size=(120,), dtype=torch.uint8)
	i = 0
	for root, dirs, files in os.walk(dirname(__file__), topdown=True):
		dirs.sort(key=lambda w: (len(w), w)) #sort by length first, then lexicographically
		files.sort(key=lambda w: (len(w), w)) #sort by length first, then lexicographically
		for filename in files:
			if filename.endswith(f'{os.extsep}pgm'):
				if i % 10 < 7:
					train_features[(i % 10) + (i // 10) * 7] = read_pgm(open(join(root, filename), 'rb')).unsqueeze(0)
					train_labels[(i % 10) + (i // 10) * 7] = (i // 10)
				else:
					test_features[((i - 7) % 10) + (i // 10) * 3] = read_pgm(open(join(root, filename), 'rb')).unsqueeze(0)
					test_labels[((i - 7) % 10) + (i // 10) * 3] = (i // 10)
				i += 1
	return train_features, train_labels, test_features, test_labels

def write_data():
	train_features, train_labels, test_features, test_labels = get_data()
	train_features_path = join(dirname(__file__), f'train_features{os.extsep}pt')
	train_labels_path = join(dirname(__file__), f'train_labels{os.extsep}pt')
	test_features_path = join(dirname(__file__), f'test_features{os.extsep}pt')
	test_labels_path = join(dirname(__file__), f'test_labels{os.extsep}pt')
	torch.save(train_features, train_features_path)
	torch.save(train_labels, train_labels_path)
	torch.save(test_features, test_features_path)
	torch.save(test_labels, test_labels_path)
	print(f'Successfully saved "{train_features_path}", "{train_labels_path}", "{test_features_path}", "{test_labels_path}"')

def train():
	n = nn.Sequential(
		nn.Flatten(),
		nn.Linear(in_features=112 * 92, out_features=40),
	)
	optimizer = torch.optim.Adam(n.parameters(), lr=0.001)

	train_features = torch.load(join(dirname(__file__), f'train_features{os.extsep}pt')).float()
	train_labels = torch.load(join(dirname(__file__), f'train_labels{os.extsep}pt')).long()
	test_features = torch.load(join(dirname(__file__), f'test_features{os.extsep}pt')).float()
	test_labels = torch.load(join(dirname(__file__), f'test_labels{os.extsep}pt')).long()

	for i in trange(1000):
		pred_train_labels = n(train_features)
		loss = F.cross_entropy(pred_train_labels, train_labels)

		optimizer.zero_grad()
		loss.backward()
		optimizer.step()

	print(f'Performance')
	with torch.no_grad():
		n.eval()
		print(f'Train performance: {(n(train_features).max(axis=1).indices == train_labels).sum().item() / len(train_labels)}')
		print(f'Test performance: {(n(test_features).max(axis=1).indices == test_labels).sum().item() / len(test_labels)}')

if __name__ == '__main__':
	seed = 0
	random.seed(seed)
	np.random.seed(seed)
	torch.manual_seed(seed)
	torch.cuda.manual_seed_all(seed)
	train()

