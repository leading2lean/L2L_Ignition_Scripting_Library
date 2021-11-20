# L2L Ignition Scripting Library
# For use integrating Ignition and the L2L (Leading2Lean) CloudDISPATCH Smart Manufacturing Platform  
# Written by Tyler Whitaker, L2L
# Created: 2021-10-30
#
# Helpful Links:
# 	L2L Support website with Best Practices: https://support.leading2lean.com/hc/en-us/articles/360051221312-Integrating-with-Ignition
# 	Our API Examples and home to this project: https://github.com/leading2lean
# 	Our corporate website: https://www.L2L.com
#
# Getting Started
# 1. Add your credentials below.
# 2. Read through the APPLICATION FUNCTIONS below to understand which functions are available for your use case.
# 3. Create Gateway Scheduled Scripts or Tag Event Scripts to send data to L2L using the APPLICATION FUNCTIONS below
# 4. Create new functions to expand the functionality to fit your needs. Feel free to submit pull requests with suggested improvements.

import urllib
from datetime import datetime, timedelta

L2L_INTEGRATION_NAME = "L2L-Ignition Scripting Library"
L2L_INTEGRATION_VERSION = "1.0"

# TODO: Update Your Credentials Here
L2L_API_SERVER_NAME = ""   						#  Put your server name here, https://<Your server name is found here.>.leading2lean.com - example: l2l, demo, l2ltest-acme
L2L_AUTH_KEY = ""	# Put your API key here
L2L_SITE = 0										# Put your site number here, Integer value, examples: 1, 2, or 25 
L2L_USERNAME = "L2L Ignition API User"				#  Put your username here, this should be the username associated with the AUTH_KEY above
 
# TODO: Replace with credentials to a sandbox site. Used for testing/debug purposes only. 
# DO NOT RUN TESTS ON A LIVE PRODUCTION SITE! FOR DEBUGGING THIS LIBRARY ONLY!
TEST_L2L_API_SERVER_NAME = ""						#  Put your server name here, https://<Your server name is found here.>.leading2lean.com - example: l2l, demo, l2ltest-acme
TEST_L2L_AUTH_KEY = ""	# Put your API key here
TEST_L2L_SITE = 0										# Put your site number here, Integer value, examples: 1, 2, or 25 
TEST_L2L_USERNAME = "L2L Ignition API User"	 			#  Put your username here, this should be the username associated with the AUTH_KEY above

# Setup Test Data
# TODO: Add test site details here. THIS DATA WILL NOT WORK IN YOUR SANDBOX!
TEST_L2L_DATA = {
	'machinecode': "1032920",
	'linecode': "Press 1",
	'productcode': "Flange01",
	'dispatchtypecode': "Code Red",
	'dispatch_description': "Houston, we have a problem!",
	'tradecode': "Mechanic",
}


class L2L_Connection:

	def __init__(self, server_name=None, auth_key=None, site=None, username=None):
		""" Class Initialization w/ API Endpoint and Credentials """
		self.l2l_api_server = "https://{server}.leading2lean.com/api/1.0/".format(server=server_name if server_name is not None else L2L_API_SERVER_NAME)
		self.auth_key = auth_key if auth_key is not None else L2L_AUTH_KEY
		self.site = site if site is not None else L2L_SITE
		self.username = username if username is not None else L2L_USERNAME

		self.system_name = system.tag.read("[System]Gateway/SystemName").value
		self.headerValues = {
			"user-agent": "{name}, version: {version}, server: {sys}".format(name=L2L_INTEGRATION_NAME, version=L2L_INTEGRATION_VERSION, sys=self.system_name),
			"content-type": "application/x-www-form-urlencoded",
		}

		self.logger = system.util.getLogger("L2L")
		self.verify_connection()


	def _debug(self, msg):
		""" Log a debug message to the L2L Ingition Log. """
		self.logger.debug(msg)
		return msg


	def _log(self, msg):
		""" Log an error to the L2L Ingition Log. """
		self.logger.error(msg)
		return msg


	#######
	# L2L API UTILITY FUNCTIONS
	#######
	def verify_connection(self):
		""" Verifies the credentials area valid for the specified site. Returns True if successful. """

		response_obj = self.make_get_request("sites/", {'site': self.site})

		# Check for success value
		if not response_obj['success']:
			raise Exception(self._log("L2L Connection Initialization Error: %(error)s".format(response_obj)))

		# Check for access to the site, should return the correct record
		if  len(response_obj['data']) <= 0 or response_obj['data'][0]['site'] == str(self.site):
			raise Exception(self._log("L2L Connection Initialization Error: site not found or no permissions to site specified"))

		# Return (success, site object)
		return (True, response_obj['data'][0])


	def make_get_request(self, api, parameters=None):
		""" Make an API GET call to the Leading2Lean API """
		if parameters is None:
			parameters = {}

		self._debug("API: {api}, GET Parameters: {params}".format(api=api, params=str(parameters)))
		parameters['auth'] = self.auth_key

		# Do HTTP GET request
		url = "{server}{api}?{params}".format(server=self.l2l_api_server, api=api, params=urllib.urlencode(parameters))
		response = system.net.httpGet(url, useCaches=False, headerValues=self.headerValues)
		response_obj = system.util.jsonDecode(response)

		self._debug("API: {api}, Response: {response}".format(api=api, response=str(response_obj)))

		# Check for success value
		if not response_obj['success']:
			raise Exception(self._log("L2L GET API: {api}, Error: {error}".format(api=api, error=response_obj['error'])))

		return response_obj


	def make_post_request(self, api, parameters=None):
		""" Make an API POST call to the Leading2Lean API """

		if parameters is None:
			parameters = {}

		self._debug("API: {api}, POST Parameters: {params}".format(api=api, params=str(parameters)))
		
		# Do HTTP  POST request using customer headers 
		url = "{server}{api}?auth={auth}".format(server=self.l2l_api_server, api=api, auth=self.auth_key)
		response = system.net.httpPost(url, "application/x-www-form-urlencoded", postData=urllib.urlencode(parameters), headerValues=self.headerValues)
		response_obj = system.util.jsonDecode(response)

		self._debug("API: {api}, Response: {response}".format(api=api, response=str(response_obj)))

		# Check for success value
		if not response_obj['success']:
			raise Exception(self._log("L2L POST API: {api}, Error: {error}".format(api=api, error=response_obj['error'])))

		return response_obj


	def format_L2L_datetime(self, value, orignal_format_hint=None):
		""" Returns a formatted datetime string for use with the L2L API """

		L2L_format = "%Y-%m-%d %H:%M:%S"  # Example: 2021-04-24 15:30:05
		common_formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%B-%dT%H:%M:%S-%H:%M", "%Y-%m-%d"]
		
		if not orignal_format_hint is None:
			dt = datetime.strptime(value, orignal_format_hint)
			return dt.strftime(L2L_format)

		# Work around for datetime objects passed in and isinstance not working correctly, just try it as a datetime to see if it works.
		# Both of these don't always work: weirdness due to ignition? version of jython?
		# 	if isinstance(value, type(datetime.now())): 
		# 	if isinstance(value, datetime): 
		try:
			result = value.strftime(L2L_format)
		except:
			result = None
		if result is not None:
			return result

		# This doesn't work properly, hack above works this out.
#		if isinstance(value, type(datetime.now())):   
#			return value.strftime(L2L_format)

		if isinstance(value, str):
			# try common formats
			for format in common_formats: 
				try:
					dt = datetime.strptime(value, format)
					return dt.strftime(L2L_format)
				except:
					# do nothing
					continue

		# Can't figure it out so throw an error
		raise Exception(self._log("L2L format_L2L_datetime Error: Invalid date value {val}".format(val=value)))

	    
	#######
	# APPLICATION FUNCTIONS
	#######

	# Sites
	# Documentation: https://support.leading2lean.com/hc/en-us/articles/360051148492-API-Documentation#Sites		
	# URL: https://<your company>.leading2lean.com/api/1.0/sites/
	# HTTP Method: GET
	def get_sites(self, site=None, parameters=None):
		""" Grab a list of sites from the API, optionally filter by site. Use the parameters dictionary for additional filters. """
		if parameters is None:
			parameters = {}

		if site is not None:
			parameters['site'] = site
			
		response = self.make_get_request("sites/", parameters)
		return response


	# Areas
	# Documentation: https://support.leading2lean.com/hc/en-us/articles/360051148492-API-Documentation#Areas		
	# URL: https://<your company>.leading2lean.com/api/1.0/areas/
	# HTTP Method: GET
	def get_areas(self, areacode=None, area_externalid=None, parameters=None):
		""" Grab a list of areas from the API, optionally filter by areacode, or area_externalid. 
		Use the parameters dictionary for additional filters. """
		if parameters is None:
			parameters = {}

		if not parameters.has_key('site'): parameters['site'] = self.site
		if areacode is not None:
			parameters['areacode'] = areacode
		if area_externalid is not None:
			parameters['externalid'] = area_externalid
			
		response = self.make_get_request("areas/", parameters)
		return response


	# Lines
	# Documentation: https://support.leading2lean.com/hc/en-us/articles/360051148492-API-Documentation#Lines		
	# URL: https://<your company>.leading2lean.com/api/1.0/lines/
	# HTTP Method: GET
	def get_lines(self, areacode=None, linecode=None, line_externalid=None, parameters=None):
		""" Grab a list of lines from the API, optionally filter by areacode, linecode, and/or line_externalid. 
		Use the parameters dictionary for additional filters. """
		if parameters is None:
			parameters = {}

		if not parameters.has_key('site'): parameters['site'] = self.site
		if areacode is not None:
			parameters['areacode'] = areacode
		if linecode is not None:
			parameters['code'] = linecode
		if line_externalid is not None:
			parameters['externalid'] = line_externalid
			
		response = self.make_get_request("lines/", parameters)
		return response


	# Machines
	# Documentation: https://support.leading2lean.com/hc/en-us/articles/360051148492-API-Documentation#Machines
	# URL: https://<your company>.leading2lean.com/api/1.0/machines/
	# HTTP Method: GET
	def get_machines(self, areacode=None, linecode=None, machinecode=None, machine_externalid=None, parameters=None):
		""" Grab a list of machines from the API, optionally filter by areacode, linecode, and/or line externalid. 
		Use the parameters dictionary for additional filters. """
		if parameters is None:
			parameters = {}

		if not parameters.has_key('site'): parameters['site'] = self.site
		if areacode is not None:
			parameters['areacode'] = areacode
		if linecode is not None:
			parameters['linecode'] = linecode
		if machinecode is not None:
			parameters['code'] = machinecode
		if machine_externalid is not None:
			parameters['externalid'] = machine_externalid
			
		response = self.make_get_request("machines/", parameters)
		return response
	

	# Machine Method: increment_cycle_count
	# Documentation: https://support.leading2lean.com/hc/en-us/articles/360051148492-API-Documentation#Machines_set_cycle_count		
	# URL: https://<your company>.leading2lean.com/api/1.0/machines/increment_cycle_count/id/?auth=<API_Key>
	# HTTP Method: POST
	# Functionality: Provides a way to increment an existing Machine's cycle count.
	# Use Case: Use this function in a gateway scheduled script to send aggregated production actual data every shift or every day. To reduce unecesary 
	#           API traffic it's not recommended use this functionality in a tag event script that may change couple of seconds.
	# Parameters:
	#	id (Required if not using code/site) - The id for the existing machine.
	#	code (Required if not using id) - Specifies the code of the existing machine.
	#	site (Required if not using id) - Specifies the site the machine is in.
	#	cyclecount - The value to increment the existing cycle count by.
	#	skip_lastupdated - If set to 1, then the lastupdated value for the machine will not be updated, otherwise it is.
	# Returns:
	# By default the API will return a json object with the following fields.
	#	success - Returns either true or false.
	#	machine - On success, returns the machine record.
	#	error (Optional) - Error message if success is false.
	def increment_cycle_count(self, machine_code, cycle_count):
		""" Increment the machine cycle count """
		parameters = {
			'site': self.site,
			'code': machine_code,
			'cyclecount': cycle_count,
			'skip_lastupdated': 1,
		}
		response = self.make_post_request("machines/increment_cycle_count/", parameters)
		return response
 

	# Machine Method: set_cycle_count
	# Documentation: https://support.leading2lean.com/hc/en-us/articles/360051148492-API-Documentation#Machines_increment_cycle_count	
	# URL: https://<your company>.leading2lean.com/api/1.0/machines/set_cycle_count/id/?auth=<API_Key>
	# HTTP Method: POST
	# Functionality: Provides a way to set an existing Machine's cycle count.
	# Use Case: Use this function in a gateway scheduled script to send aggregated production actual data every shift or every day. To reduce unecesary 
	#           API traffic it's not recommended use this functionality in a tag event script that may change couple of seconds.
	# Parameters:
	# 	id (Required if not using code/site) - The id for the existing machine.
	# 	code (Required if not using id) - Specifies the code of the existing machine.
	# 	site (Required if not using id) - Specifies the site the machine is in.
	# 	cyclecount - The new value for the cycle count.
	# 	skip_lastupdated - If set to 1, then the lastupdated value for the machine will not be updated, otherwise it is.
	# Returns:
	# By default the API will return a json object with the following fields.
	# 	success - Returns either true or false.
	# 	machine - On success, returns the machine record.
	# 	error (Optional) - Error message if success is false.
	def set_cycle_count(self, machine_code, cycle_count):
		""" Set the machine cycle count """
		parameters = {
			'site': self.site,
			'code': machine_code,
			'cyclecount': cycle_count,
			'skip_lastupdated': 1,
		}
		response = self.make_post_request("machines/set_cycle_count/", parameters)
		return response


	# Pitch Details Method: record_details
	# Documentation: https://support.leading2lean.com/hc/en-us/articles/360051148492-API-Documentation#Pitch%20Details_record_details	
	# URL: https://<your company>.leading2lean.com/api/1.0/pitchdetails/record_details/?auth=<API_Key>
	# HTTP Method: GET or POST
	# Functionality: Provides a way to record product part completion and scrap counts. 
	# Use Case: Use this function in a gateway scheduled script to send aggregated production actual data every 1 to 3 minutes. To reduce unecesary 
	#           API traffic it's not recommended use this functionality in a tag event script that may change couple of seconds.
	# Parameters:
	# 	auth (Required) – This is your authentication (API Key).
	# 	site (Required) – Specify the site code for the data you are reporting
	# 	linecode (Required if not providing line_externalid) – Specify the line code for the line you are reporting actuals
	# 	line_externalid (Required if not providing linecode) – Specify the line externalid for the line you are reporting actuals
	# 	start (Required) – The start of the reporting interval using this format: "%Y-%m-%d %H:%M:%S.%f" or "%Y-%m-%d %H:%M:%S" Example: 2013-04-24 15:30:05.153005 or 2013-04-24 15:30:05
	# 	end (Required) – The end of the reporting interval using this format: "%Y-%m-%d %H:%M:%S.%f" or "%Y-%m-%d %H:%M:%S" Example: 2013-04-24 15:30:05.153005 or 2013-04-24 15:30:05. The end value must come after the start value.
	# 	actual (Optional) – The decimal value (up to 2 digits after the .) representing the products produced I.e. 2.0, 1453.74, 54, etc. Defaults to 0.00
	# 	scrap (Optional) – The decimal value (up to 2 digits after the .) representing the products produced I.e. 2.0, 1453.74, 54, etc. Defaults to 0.00
	# 	operator_count (Optional) – The decimal value (up to 2 digits after the .) representing the products produced I.e. 2.0, 1453.74, 54, etc. Defaults to 0.00
	# 	productcode (Required) – The product code/sku/model number being produced. Defaults to null.
	# 	format=xml (Optional) – Returns the results in xml format instead of json.
	# Returns:
	# By default the API will return a json object with the following fields.
	# 	success - Returns either true or false.
	# 	data - On success, returns the individual record saved.
	# 	error (Optional) - Error message if success is false.
	def record_pitch_details(self, line_code, line_externalID, start_datetime, end_datetime, product_code, actual_parts_produced=None, scrap_count=None, operator_count=None):
		""" Send L2L my production numbers """
		
		if (actual_parts_produced is None and scrap_count is None and operator_count is None):
			return  False  # do nothing since we are not recording any data
		
		parameters = {
			'site': self.site,
			'start': self.format_L2L_datetime(start_datetime),
			'end': self.format_L2L_datetime(end_datetime),
			'productcode': product_code,
		}

		if (parameters['start'] > parameters['end']):
			raise Exception(self._log("L2L record_pitch_details Error: start must be before end"))

		if line_code is not None:
			parameters['linecode'] = line_code
		else:
			parameters['line_externalid'] = line_externalID
		if actual_parts_produced is not None: 
			parameters['actual'] = actual_parts_produced
		if scrap_count is not None:
			parameters['scrap'] = scrap_count
		if operator_count is not None:
			parameters['operator_count'] = operator_count
		
		response = self.make_get_request("pitchdetails/record_details/", parameters)
		return response


	# Dispatch Method: 
	# Documentation: https://support.leading2lean.com/hc/en-us/articles/360051148492-API-Documentation#Dispatches_open	
	# URL: https://<your company>.leading2lean.com/api/1.0/dispatches/open/?auth=<API_Key>
	# HTTP Method: POST
	# Functionality: Provides a way to open a new dispatch. 
	# Use Case: Use this function in a tag event script when a tag value exceeds a given threshold indicating a problem has occurred that needs resolution.
	# Parameters:
	#	 dispatchtypecode (Required if no dispatchtype id is provided) - Specify the dispatch type code that you want to create.
	#	 dispatchtype (Required if no dispatchtypecode is provided) - Specify the dispatch type id that you want to create.
	#	 description (Required) - This is the dispatch description. I.e. What is the problem, work order description, etc.
	#	 machinecode (Required if no machine id is provided) - This is the machine code this dispatch is related to.
	#	 machine (Required if no machinecode is provided) - This is the machine id this dispatch is related to.
	#	 tradecode (Required if no trade id is provided) - This is the trade code this dispatch is related to.
	#	 trade (Required if no tracecode is provided) - This is the trade id this dispatch is related to.
	#	 user (Required) - This is the username of the user creating the dispatch.
	#	 site (Required) - This is the site this dispatch is related to.
	#	 auth (Required) - This is your authentication (API Key).
	#	 trade_required (Optional) - If thise is set to true, we will validate that the trade supplied is valid and return an error if not. If this parameter is not supplied or set to false, we will attempt to use the provided trade and fall back to the default trade if it is invalid.
	#	 reason_id (Optional) - This is the reason id this dispatch is related to.
	#	 document_externalid (Optional) - This is the externalid value of an existing document in Document Center.
	#	 assigned_users (Optional) - This is a comma delimited list of usernames of the users you want assigned to this dispatch. For example: assigned_users=khill,jseaton
	#	 due (Optional) – The due date of the dispatch in this format: "%Y-%m-%d %H:%M" Example: 2013-04-24 15:30. Must be in the site's timezone.
	#	 reported (Optional) – The reported date of the dispatch in one of these two formats: "%Y-%m-%d %H:%M:%S" or "%Y-%m-%d %H:%M" Examples: 2013-04-24 15:30:00 or 2013-04-24 15:30. If not specified then the current site time is used. If specified, it must be in the site's timezone.
	#	 parent_dispatch_id (Optional) – The id of a dispatch to set as the parent dispatch.
	#	 last_part_run (Optional) - This is the last part run value to be associated with the dispatch.
	#	 material_quarantined (Optional) - This is the material quarantined value to be associated with the dispatch. Possible values are 'N' and 'Y'.
	#	 Optional Query Parameter (Optional) - Add key/value query parameter to the end of the url.
	#	 format=xml (Optional) - returns the results in xml format instead of json.
	# Returns:
	# By default the API will return a json object with the following fields.
	#	 success - Returns either true or false.
	#	 data - On success, returns the individual dispatch record created.
	#	 error (Optional) - Error message if success is false.
	def open_dispatch(self, dispatchtypecode, description, machinecode, tradecode=None, username=None):
		""" Open a new Dispatch in CloudDISPATCH """

		parameters = {
			'site': self.site,
			'dispatchtypecode': dispatchtypecode,
			'description': description,
			'machinecode': machinecode,
			'tradecode': tradecode,
			'trade_required': False,
			'user': username if username is not None else self.username,
		}
	
		response = self.make_post_request("dispatches/open/", parameters)
		return response



####################
# Internal tests for the L2L Connection Class
# Usage: You can run these tests from the script console in the designer. 
# 		Debug output is viewable in the Output Console and Diagnostics windows.
# 		Make sure you setup the test data and config at the top of this file.
# Script console example:
# 		test = L2L.Test_L2L_Connection_Class()
# 		test.run_all_tests()
####################
class Test_L2L_Connection_Class():
	""" Internal Tests to verify the L2L_Connection works properly. """
	
	def __init__(self, server_name=None, auth_key=None, site=None, username=None):
		""" Test Initialization w/ API Endpoint and Credentials """
		
		self.server_name = server_name if server_name is not None else TEST_L2L_API_SERVER_NAME
		self.auth_key = auth_key if auth_key is not None else TEST_L2L_AUTH_KEY
		self.site = site if site is not None else TEST_L2L_SITE
		self.username = username if username is not None else TEST_L2L_USERNAME

		# Create L2L Connection
		self.logger = system.util.getLogger("L2L")
		self.l2l = L2L.L2L_Connection(server_name, auth_key, site, username)
		
		# Setup Test Data
		self.machinecode = TEST_L2L_DATA['machinecode']
		self.linecode = TEST_L2L_DATA['linecode']
		self.productcode = TEST_L2L_DATA['productcode']
		self.dispatchtypecode = TEST_L2L_DATA['dispatchtypecode']
		self.dispatch_description = TEST_L2L_DATA['dispatch_description']
		self.tradecode = TEST_L2L_DATA['tradecode']
		self.field_params = {'fields': 'code,description'}


	def _debug(self, msg):
		""" Log a debug message to the L2L Ingition Log. """
		self.logger.debug(msg)
		print msg
		return msg


	def _log(self, msg):
		""" Log an error to the L2L Ingition Log. """
		self.logger.error(msg)
		print msg
		return msg		


	def run_all_tests(self):
		""" Run all the tests """
		self._debug("run_all_tests")
		self.test_machine_cycle_count()
		self.test_format_L2L_datetime()
		self.test_get_sites()
		self.test_get_areas()
		self.test_get_lines()
		self.test_get_machines()
		self.test_record_pitch_details()
		self.test_open_dispatch()
		self._debug("run_all_tests - Completed")
		

	def test_machine_cycle_count(self):
		""" Test the machine cycle count APIs """
		self._debug("test_machine_cycle_count")
		response = self.l2l.increment_cycle_count(self.machinecode, 4)
		self._debug(str(response))
		response = self.l2l.set_cycle_count(self.machinecode, 13)
		self._debug(str(response))


	def test_format_L2L_datetime(self):
		""" Test the format_L2L_datetime function """
		self._debug("test_format_L2L_datetime")
		now = datetime.now()
		self.l2l.format_L2L_datetime(now)
		self.l2l.format_L2L_datetime("2021-04-24T15:30:05")
		self.l2l.format_L2L_datetime("2021-04-24")
		self.l2l.format_L2L_datetime("2021-04-24T", "%Y-%m-%dT")
		

	def test_get_sites(self):
		""" Test the get_sites function """
		self._debug("test_get_sites")
		data = self.l2l.get_sites(25, parameters=self.field_params)
		self._debug(str(data))


	def test_get_areas(self):
		""" Test the test_get_areas function """
		self._debug("test_get_areas")
		data = self.l2l.get_areas(parameters=self.field_params)
		self._debug(str(data))


	def test_get_lines(self):
		""" Test the test_get_lines function """
		self._debug("test_get_lines")
		data = self.l2l.get_lines(parameters=self.field_params)
		self._debug(str(data))

		
	def test_get_machines(self):
		""" Test the test_get_machines function """
		self._debug("test_get_machines")
		data = self.l2l.get_machines(parameters=self.field_params)
		self._debug(str(data))
		

	def test_record_pitch_details(self):
		""" Test the record_pitch_details function """
		self._debug("test_record_pitch_details")
		line_code = "Press 1"
		line_externalID = None
		start_datetime = datetime.now()
		end_datetime = start_datetime + timedelta(seconds=1)
		actual_parts_produced = 3
		scrap_count = 1
		operator_count = 1
		data = self.l2l.record_pitch_details(self.linecode, line_externalID, start_datetime, end_datetime, self.productcode, actual_parts_produced, scrap_count, operator_count)
		self._debug(str(data))


	def test_open_dispatch(self):
		""" Test the test_open_dispatch function """
		self._debug("test_open_dispatch")
		data = None
		try:
			data = self.l2l.open_dispatch(self.dispatchtypecode, self.dispatch_description, self.machinecode, self.tradecode, self.username)
		except Exception as error:
			# raise all errors except for if a duplicate cirtical disatch is already open
			if str(error).find("This Machine already has an open critical Dispatch.") == -1:
				raise Exception(error)
		self._debug(str(data))
