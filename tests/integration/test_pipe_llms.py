# Copyright 2023-present, Argilla, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Dict, Generator, List

from distilabel.pipeline.llm.openai import OpenAILLM
from distilabel.pipeline.llm.transformers import TransformersLLM
from distilabel.pipeline.local import Pipeline
from distilabel.pipeline.step.base import Step, StepInput
from distilabel.pipeline.step.generators.huggingface import LoadHubDataset
from distilabel.pipeline.step.task.generation import TextGeneration


class RenameColumns(Step):
    @property
    def inputs(self) -> List[str]:
        return []

    @property
    def outputs(self) -> List[str]:
        return list(self._runtime_parameters.get("rename_mappings", {}).values())

    def process(
        self, inputs: StepInput, rename_mappings: dict
    ) -> Generator[List[Dict[str, Any]], None, None]:
        outputs = []
        for input in inputs:
            outputs.append({rename_mappings.get(k, k): v for k, v in input.items()})
        yield outputs


def test_pipeline_with_llms_serde():
    with Pipeline() as pipeline:
        load_hub_dataset = LoadHubDataset(name="load_dataset")
        rename_columns = RenameColumns(name="rename_columns")
        load_hub_dataset.connect(rename_columns)

        generate_response = TextGeneration(
            name="generate_response",
            llm=OpenAILLM(api_key="sk-***"),
            output_mapping={"generation": "output"},
        )
        rename_columns.connect(generate_response)

        generate_response_mini = TextGeneration(
            name="generate_response_mini",
            llm=TransformersLLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0"),
            output_mapping={"generation": "output"},
        )
        rename_columns.connect(generate_response_mini)
        dump = pipeline.dump()

    with Pipeline() as pipe:
        pipe = pipe.from_dict(dump)

    assert "load_dataset" in pipe.dag.G
    assert "rename_columns" in pipe.dag.G
    assert "generate_response" in pipe.dag.G
    assert "generate_response_mini" in pipe.dag.G
