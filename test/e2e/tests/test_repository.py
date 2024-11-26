# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may
# not use this file except in compliance with the License. A copy of the
# License is located at
#
# 	 http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

"""Integration tests for the ECR Public Repository API.
"""

import pytest
import time
import logging

from acktest.resources import random_suffix_name
from acktest.k8s import resource as k8s
from acktest.aws.identity import get_account_id

from e2e import service_marker, CRD_GROUP, CRD_VERSION, load_ecrpublic_resource
from e2e.replacement_values import REPLACEMENT_VALUES
from e2e.bootstrap_resources import get_bootstrap_resources
from e2e.tests.helper import ECRPublicValidator

RESOURCE_PLURAL = "repositories"

CREATE_WAIT_AFTER_SECONDS = 10
UPDATE_WAIT_AFTER_SECONDS = 10
DELETE_WAIT_AFTER_SECONDS = 10

@pytest.fixture(scope="module")
def simple_repository(ecrpublic_client):

    resource_name = random_suffix_name("ecr-repository", 24)

    replacements = REPLACEMENT_VALUES.copy()
    replacements["REPOSITORY_NAME"] = resource_name

    resource_data = load_ecrpublic_resource(
        "repository",
        additional_replacements=replacements,
    )

    logging.debug(resource_data)

    # Create k8s resource
    ref = k8s.CustomResourceReference(
        CRD_GROUP, CRD_VERSION, RESOURCE_PLURAL,
        resource_name, namespace="default",
    )
    k8s.create_custom_resource(ref, resource_data)
    cr = k8s.wait_resource_consumed_by_controller(ref)

    assert cr is not None
    assert k8s.get_resource_exists(ref)

    yield (ref, cr, resource_name)

    _, deleted = k8s.delete_custom_resource(
        ref,
        period_length=DELETE_WAIT_AFTER_SECONDS,
    )
    assert deleted
    time.sleep(DELETE_WAIT_AFTER_SECONDS)

    validator = ECRPublicValidator(ecrpublic_client)
    assert not validator.repository_exists(resource_name)


@service_marker
@pytest.mark.canary
class TestRepository:
    def test_create_delete(self, simple_repository, ecrpublic_client):
        (ref, cr, repository_name) = simple_repository
        resource_name = ref.name

        # Check ECR Repository exists
        validator = ECRPublicValidator(ecrpublic_client)
        assert validator.repository_exists(resource_name)
        assert cr is not None
        assert 'spec' in cr
        assert 'tags' in cr["spec"]
        assert len(cr["spec"]["tags"]) == 1
        assert 'status' in cr
        assert 'ackResourceMetadata' in cr["status"]
        assert 'arn' in cr["status"]["ackResourceMetadata"]
        arn = cr["status"]["ackResourceMetadata"]["arn"]
        tags = validator.get_repository_tags(arn)
        assert len(tags) == len(cr["spec"]["tags"]) + 2

        # Update tags
        updates = {
            "spec": {
                "tags": [
                    {
                        "key": "test",
                        "value": "test"
                    },
                    {
                        "key": "key",
                        "value": "value"
                    },
                ]
            }
        }
        k8s.patch_custom_resource(ref, updates)
        time.sleep(UPDATE_WAIT_AFTER_SECONDS)

        cr = k8s.wait_resource_consumed_by_controller(ref)
        assert cr is not None
        assert 'spec' in cr
        assert 'tags' in cr["spec"]
        assert len(cr["spec"]["tags"]) == 2
        tags = validator.get_repository_tags(arn)
        assert len(tags) == len(cr["spec"]["tags"]) + 2
