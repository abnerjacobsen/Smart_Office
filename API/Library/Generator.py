"""This module is used as a generator for ID's, but may in future include other features also."""

import random

def generateID():
		"""Randomly generates a six character long id from provided data"""

		idLength = 6
		idData = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
		id = ""
		for x in range(idLength):
			id = id + idData[random.randint(0, len(idData)-1)]
		return id