# Copyright 2018-2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.
from __future__ import absolute_import

import os

import pytest
from sagemaker import utils
from ... import MXNetWrapper as MXNet

from ...integration import RESOURCE_PATH
from .timeout import timeout

DATA_PATH = os.path.join(RESOURCE_PATH, 'mnist')
SCRIPT_PATH = os.path.join(DATA_PATH, 'mnist.py')


@pytest.mark.model("mnist")
@pytest.mark.integration("smexperiments")
@pytest.mark.skip_test_in_region
def test_training(sagemaker_regions, ecr_image, instance_type, instance_count, framework_version):
    hyperparameters = {'sagemaker_parameter_server_enabled': True} if instance_count > 1 else {}
    hyperparameters['epochs'] = 1

    mx = MXNet(entry_point=SCRIPT_PATH,
               role='SageMakerRole',
               instance_count=instance_count,
               instance_type=instance_type,
               sagemaker_regions=sagemaker_regions,
               image_uri=ecr_image,
               framework_version=framework_version,
               hyperparameters=hyperparameters)

    mx = _disable_sm_profiler(mx.sagemaker_session.boto_region_name, mx)

    with timeout(minutes=15):
        prefix = 'mxnet_mnist/{}'.format(utils.sagemaker_timestamp())
        train_input = mx.sagemaker_session.upload_data(path=os.path.join(DATA_PATH, 'train'),
                                                       key_prefix=prefix + '/train')
        test_input = mx.sagemaker_session.upload_data(path=os.path.join(DATA_PATH, 'test'),
                                                      key_prefix=prefix + '/test')

        job_name = utils.unique_name_from_base('test-mxnet-image')
        mx.fit({'train': train_input, 'test': test_input}, job_name=job_name)


def _disable_sm_profiler(region, estimator):
    """Disable SMProfiler feature for China regions
    """

    if region in ('cn-north-1', 'cn-northwest-1'):
        estimator.disable_profiler = True
    return estimator
