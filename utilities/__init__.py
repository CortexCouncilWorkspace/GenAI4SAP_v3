# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import configparser
import os
import sys

module_path = os.path.abspath(os.path.join('.'))
sys.path.append(module_path)
config = configparser.ConfigParser()
config.read(module_path+'/config/config.ini')

# [GLOBAL]
PROJECT_ID = config['CONFIG']['PROJECT_ID']
REGION_ID = config['CONFIG']['REGION_ID']
MODEL = config['CONFIG']['MODEL'] 
LANGUAGE = config['CONFIG']['LANGUAGE']

#[BIGQUERY]
BQ_DATASET_ID = config['BIGQUERY']['BQ_DATASET_ID']
BQ_REGION_ID = config['BIGQUERY']['BQ_REGION_ID']
BQ_TABLE_LIST = config['BIGQUERY']['BQ_TABLE_LIST']

#[CLOUDRUN]
CHROMA_DATA_BUCKET = config['CLOUDRUN']['CHROMA_DATA_BUCKET']
SERVICE_ACCOUNT_NAME = config['CLOUDRUN']['SERVICE_ACCOUNT_NAME']
CLOUDRUN_APP_NAME = config['CLOUDRUN']['CLOUDRUN_APP_NAME']
SECRET_NAME = config['CLOUDRUN']['SECRET_NAME']


#[API_KEY]
API_KEY = config['API_AUTH']['API_KEY']

#[PERSONALIZATION]
LOGO_URL = config['PERSONALIZATION']['LOGO_URL']
APP_TITLE = config['PERSONALIZATION']['APP_TITLE']
APP_SUBTITLE = config['PERSONALIZATION']['APP_SUBTITLE']



__all__ = ["PROJECT_ID",
           "REGION_ID",
           "MODEL",
           "LANGUAGE",
           "BQ_DATASET_ID",
           "BQ_REGION_ID",
           "BQ_TABLE_LIST",
           "CHROMA_DATA_BUCKET",
           "SERVICE_ACCOUNT_NAME",
           "CLOUDRUN_APP_NAME",
           "SECRET_NAME",
           "LOGO_URL",
           "APP_TITLE",
           "APP_SUBTITLE"
           "API_KEY"
           "root_dir",
           "save_config"]