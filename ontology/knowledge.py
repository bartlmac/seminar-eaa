"""Evidence-backed extraction contract, separate from calculation inputs."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from ontology.tbox import TBOX_VERSION


class Structure(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Evidence(Structure):
    file: str = Field(min_length=1, description='Project-relative path to a hashed export artifact.')
    location: str = Field(min_length=1, description='Sheet!Cell or Sheet!Range, defined name, or VBA function and line numbers.')


class Mapping(Structure):
    quantity: str = Field(min_length=1)
    role: Literal['input', 'parameter', 'table_input', 'scalar_output', 'trajectory_output']
    source_name: str = ''
    evidence: list[Evidence] = Field(min_length=1)
    note: str = ''


class Rule(Structure):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    affects: list[str] = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)
    confidence: Literal['direct_evidence', 'interpretation']


class Dataset(Structure):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class OpenQuestion(Structure):
    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    impact: str = Field(min_length=1)
    blocks_porting: bool
    evidence: list[Evidence] = Field(min_length=1)


class Symbol(Structure):
    symbol: str = Field(min_length=1)
    meaning: str = Field(min_length=1)
    reference: str = Field(min_length=1, description='T-Box field, local helper, constant or table lookup.')


class WorksheetFormula(Structure):
    source_formula: str = Field(pattern='^=')
    evidence: Evidence
    applies_to: str | None = Field(default=None, description='Optional Sheet!A1:A50 family; every formula must be checked by relative translation.')


class Formula(Structure):
    id: str = Field(min_length=1)
    target: str = Field(min_length=1, description='Output or helper; helper names do not extend the T-Box.')
    latex: str = Field(min_length=1)
    symbols: list[Symbol] = Field(min_length=1)
    worksheet_formulas: list[WorksheetFormula] = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1, description='Include VBA evidence for called functions.')
    conditions: str = Field(min_length=1)
    timing: str = Field(min_length=1)
    status: Literal['documented', 'incomplete']
    open_questions: list[str] = Field(default_factory=list)


class KnowledgeExtract(Structure):
    schema_version: Literal['endowment.knowledge.v1']
    tbox_version: Literal[TBOX_VERSION]
    source_file: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    mappings: list[Mapping] = Field(min_length=1)
    rules: list[Rule] = Field(min_length=1)
    datasets: list[Dataset] = Field(min_length=1)
    formulas: list[Formula] = Field(min_length=1)
    open_questions: list[OpenQuestion]
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode='after')
    def consistent_ids(self):
        pairs = [(m.quantity, m.role) for m in self.mappings]
        if len(pairs) != len(set(pairs)):
            raise ValueError('Duplicate quantity/role mapping.')
        for group in (self.rules, self.datasets, self.formulas, self.open_questions):
            ids = [item.id for item in group]
            if len(ids) != len(set(ids)):
                raise ValueError('Duplicate statement IDs.')
        questions = {q.id for q in self.open_questions}
        for formula in self.formulas:
            if set(formula.open_questions) - questions:
                raise ValueError('Formula refers to an unknown open question.')
            if formula.status == 'incomplete' and not formula.open_questions:
                raise ValueError('An incomplete formula needs an open question.')
        return self
