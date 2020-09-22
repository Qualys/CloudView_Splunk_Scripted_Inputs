# This is an example scriptlet to pull AWS accounts
# Pulls a list of connector from /cloudview-api/rest/v1/aws/connectors
# Iterates the list of connectors per control per resource evaluations
# This example can be used for Azure or GCP by changing out the Cloud Provider and field map for account/subscription/project


import json, os, requests, base64, time, logging, yaml
import logging.config
from socket import error as SocketError
import errno

# setup_http_session sets up global http session variable for HTTP connection sharing
def setup_http_session():
    global httpSession

    httpSession = requests.Session()

# setup_credentials builds HTTP auth string and base64 encodes it to minimize recalculation
def setup_credentials(username, password):
    global httpCredentials

    usrPass = str(username)+':'+str(password)
    usrPassBytes = bytes(usrPass, "utf-8")
    httpCredentials = base64.b64encode(usrPassBytes).decode("utf-8")

def setup_logging(default_path='./config/logging.yml',default_level=logging.INFO,env_key='LOG_CFG'):
    """Setup logging configuration"""
    if not os.path.exists("log"):
        os.makedirs("log")
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

# Start main
setup_logging()
logger = logging.getLogger(__name__)

#Declare globals
global httpCredentials
global httpSession



# Set Qualys API Credentials and URL
#username = "QUALYS_API_USERNAME"
#password = "QUALYS_API_PASSWORD"
#BASEURL = "QUALYS_API_URL"
# use the below variable assignement if you are using os environment variables for storing the Qualys API User name and Password values
username = os.environ["QUALYS_API_USERNAME"]
password = os.environ["QUALYS_API_PASSWORD"]
BASEURL = os.environ["QUALYS_API_URL"]   #including https:// in API URL
#############################

# Tracking Variables
pageNum = 0
CompleteList = False
errorCount = 0
#############################

#Set Retry LImit for API Calls
retryLimit = 5
#############################

#Set Time Space in hours for data collection - # hours from now
hoursBack = 8
#############################

#Specify Cloud Service Provider
provider="aws"
accountType={
    "aws": "awsAccountId",
    "azure": "subscriptionId",
    "gcp": "projectId"
}
#############################

# Setup API Session Credentials
setup_http_session()
setup_credentials(username, password)

# Setup Headers for API Calls
headers = {
    'Accept': '*/*',
    'content-type': 'application/json',
    'Authorization': "Basic %s" % httpCredentials
}

# Main

#loop to paginate through list of account
while not CompleteList:
    URL =  "{}/cloudview-api/rest/v1/{}/connectors?pageNo={}&pageSize=50".format(BASEURL,str(provider),str(pageNum))
    logger.debug ("Account list URL: {}".format(URL))
    apiResponse = False
    retryCount = 0
    while not apiResponse:
        accountList = httpSession.get(URL, headers=headers, verify=True)
        logger.debug ("\n\nStatus code {} for {}\n\n".format(accountList.status_code, URL))
        if accountList.status_code == 200:
            apiResponse = True
        else:
            errorCount += 1
            time.sleep(30)
            retryCount+=1
        if retryCount > retryLimit:
            logger.warning("Retry Count Exceeded Code {} on GET {}".format(str(accountList.status_code), URL))
            #break
            apiResponse = True
    logger.info ("Status Code: {}".format(accountList.status_code))
    logger.debug ("Raw response from connector lists: {}".format(accountList.text))
    response = json.loads(accountList.text)
    logger.debug ("Response from connector lists: {}".format(response))

    for account in response['content']:
        URL2 = "{}/cloudview-api/rest/v1/{}/evaluations/{}?pageSize=300".format(BASEURL,str(provider),str(account[str(accountType[provider])]))
        logger.debug ("Account list URL: {}".format(URL2))
        apiResponse2 = False
        retryCount = 0
        while not apiResponse2:

            eval = httpSession.get(URL2, headers=headers, verify=True)
            logger.info ("\n\nStatus code {} for {}\n\n".format(eval.status_code, URL2))
            if eval.status_code == 200:
                apiResponse2 = True
            else:
                errorCount += 1
                time.sleep(30)
                retryCount+=1
            if retryCount > retryLimit:
                logger.warning("Retry Count Exceeded Code {} on GET {}".format(str(eval.status_code), URL2))
                #break
                apiResponse2 = True
        logger.info ("Status Code: {}".format(eval.status_code))
        logger.debug ("Raw response from CID for Account {}: {}".format(account[str(accountType[provider])], eval.text))
        evalcontent = json.loads(eval.text)
        logger.debug (type(evalcontent))
        evalcontentlist = evalcontent['content']
        logger.debug (type(evalcontentlist))
        logger.info ("\nLength of evalcontentlist {}\n".format(len(evalcontentlist)))
        logger.debug ("Response from CID for Account {}: {}".format(account[str(accountType[provider])],evalcontent))

        try:
            for i in evalcontentlist:
                cid = int(i["controlId"])
                criticality = str(i["criticality"])
                remediationURL = str(BASEURL) + "/cloudview/controls/cid-" + str(i["controlId"]) + ".html"
                notCompleteListResources = True
                resourcePage = 0
                resourceEvalList = []
                #loop to paginate through list of resource evaluations per control
                if int(i['passedResources']) > 0 or int(i['failedResources']) > 0:
                    while notCompleteListResources:

                        URL3 = "{}/cloudview-api/rest/v1/{}/evaluations/{}/resources/{}?pageNo={}&pageSize=100&filter=evaluatedOn%3A%5Bnow-{}h..now-1s%5D".format(BASEURL,str(provider),str(account[str(accountType[provider])]),cid, str(resourcePage),str(hoursBack))

                        logger.info ("Account {} CID URL: {}".format(str(account[str(accountType[provider])]) ,URL3))
                        apiResponse3 = False
                        retryCount = 0
                        while not apiResponse3:
                            try:
                                result = httpSession.get(URL3, headers=headers, verify=True)
                                logger.info ("\nStatus code {} for {}\n".format(result.status_code, URL3))
                            except Exception as x:
                                logger.error("\nException Encountered\n")
                                logger.error("\nError {} {}".format(x, str(x.__class__.__name__)))
                                errorCount+= 1
                                #retryCount+=1
                                logger.debug("trying again")
                                #pass
                            #except:
                            #    logger.error("Unexpected error")
                            #    break
                            else:
                                logger.info("GET {} Response Code {}".format(URL3,result.status_code))
                                #break
                            if result.status_code == 200:
                                apiResponse3 = True
                            else:
                                logger.debug("GET Response - {}".format(result.text))
                                errorCount+=1
                                time.sleep(10)
                                retryCount+=1
                            if retryCount > retryLimit:
                                logger.warning("Retry Count Exceeded Code {} on GET {}".format(str(result.status_code), URL3))
                                #break
                                apiResponse = True
                        #logger.debug (result)
                        logger.debug ("\nRaw ResourceEvaluation = {}\n".format(result.text))
                        resourceevaluation = json.loads(result.text)
                        logger.debug ("\nResourceEvaluation = {}\n".format(resourceevaluation))
                        if resourceevaluation['content']:
                            resourceEvalList.extend(resourceevaluation['content'])

                        if resourceevaluation['last'] and resourceEvalList:
                            sanityCheck = 0
                            resourcecontent = {}
                            logger.debug ("\nFull List of CID Evaluations = {} \n".format(str(resourceEvalList)))
                            count = len(resourceEvalList)
                            if count > 0:
                                logger.info ("\n\nAccount {} - Resource CID {} Evaluations Count - {}".format(account[str(accountType[provider])],str(cid),count))
                                for evals in resourceEvalList:
                                    #logger.debug ("\n evals type {}\n".format(type(evals)))
                                    resourcecontent = {}
                                    resourcecontent.update(evals)
                                    resourcecontent["controlName"] = i["controlName"]
                                    resourcecontent["controlId"] = i["controlId"]
                                    resourcecontent["remediationURL"] = remediationURL
                                    resourcecontent["name"] = account["name"]
                                    resourcecontent["criticality"] = criticality
                                    print ((json.dumps(resourcecontent)))
                                    sanityCheck+=1
                                logger.info ("\n Number of items in the list: {} \n".format(sanityCheck))
                                notCompleteListResources = False

                        else:
                            resourcePage+=1


        except Exception as e:
            logger.debug("Error encountered: {}".format(e))
            errorCount+=1
            #pass

        except SocketError as e:
            if e.errno != errno.ECONNRESET:
                raise # Not error we are looking for
            else:
                pass # Handle error here.

    if response['last']:
        logger.debug ("Error Count on API Requests: {}".format(errorCount))
        CompleteList = True
    else:
        pageNum+=1
