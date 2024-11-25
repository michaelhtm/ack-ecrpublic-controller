# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may
# not use this file except in compliance with the License. A copy of the
# License is located at
#
#	 http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

"""Helper functions for ECRPublic e2e tests
"""

import logging

class ECRPublicValidator:
    def __init__(self, ecrpublic_client):
        self.ecrpublic_client = ecrpublic_client

    def get_repository(self, repository_name: str):
        try:
            response = self.ecrpublic_client.describe_repositories(
                repositoryNames=[repository_name]
            )
            if len(response["repositories"]) == 0:
                return None
            return response["repositories"][0]
        except Exception as e:
            logging.error(f"Error: {e}")
            return None
    
    def repository_exists(self, repository_name: str):
        return self.get_repository(repository_name) is not None
    
    def get_repository_tags(self, repository_arn: str):
        try:
            response = self.ecrpublic_client.list_tags_for_resource(
                resourceArn=repository_arn
            )
            if len(response["tags"]) == 0:
                return None
            return response["tags"]
        except Exception as e:
            logging.error(f"Error: {e}")
            return None