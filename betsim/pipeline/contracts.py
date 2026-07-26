from dataclasses import dataclass


@dataclass(frozen=True)
class DriftDetection:
    evidence: str


@dataclass(frozen=True)
class TrainingResult:
    version: str


@dataclass(frozen=True)
class ModelEvaluation:
    champion_version: str
