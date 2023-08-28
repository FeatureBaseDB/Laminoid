import os
import sys
import random
import string
import time

import requests
from string import Template

import config

# parse helper
def find_between(s, first, last):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""


# random strings
def random_string(size=6, chars=string.ascii_letters + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))


###############
# FeatureBase #
###############
def apply_schema(list_of_lists, schema):
	result = []
	for row in list_of_lists:
		dict_row = {}
		for i, val in enumerate(row):
			dict_row[schema[i]] = val
		result.append(dict_row)
	return result

# "sql" key in document should have a valid query
def featurebase_query(document):
	# try to run the query
	try:
		sql = document.get("sql")

		# Specify the file path where you want to save the SQL string
		"""
		file_path = "output.sql"

		# Open the file in write mode
		with open(file_path, "a") as file:
			# Write the SQL string to the file
			file.write("%s\n" % sql)
		"""

		result = requests.post(
			config.featurebase_endpoint+"/query/sql",
			data=sql.encode('utf-8'),
			headers={
				'Content-Type': 'text/plain',
				'X-API-Key': '%s' % config.featurebase_token,
			}
		).json()

	except Exception as ex:
		# bad query?
		exc_type, exc_obj, exc_tb = sys.exc_info()
		document['error'] = "%s: %s" % (exc_tb.tb_lineno, ex)
		return document

	if result.get('error', ""):
		# featurebase reports and error
		document['explain'] = "Error returned by FeatureBase: %s" % result.get('error')
		document['error'] = result.get('error')
		document['data'] = result.get('data')

	elif result.get('data', []):
		# got some data back from featurebase
		document['data'] = result.get('data')
		document['schema'] = result.get('schema')

		field_names = []

		for field in result.get('schema').get('fields'):
			field_names.append(field.get('name'))

		document['results'] = apply_schema(result.get('data'), field_names)
	
	else:
		document['explain'] = "Query was successful, but returned no data."

	return document

