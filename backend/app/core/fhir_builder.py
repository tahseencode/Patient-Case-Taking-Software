import uuid
from typing import Dict, Any, List
from datetime import datetime
from backend.app.models.schemas import PatientDemographics, StructuredClinicalSummary, DoctorConsultationRecord

class ABDMFHIRBuilder:
    @staticmethod
    def build_fhir_bundle(
        patient: PatientDemographics,
        summary: StructuredClinicalSummary,
        consultation: Optional[DoctorConsultationRecord] = None
    ) -> Dict[str, Any]:
        bundle_id = f"ABDM-BUNDLE-{uuid.uuid4().hex[:12].upper()}"
        now_iso = datetime.now().isoformat() + "Z"

        entries: List[Dict[str, Any]] = []

        # 1. Composition Resource (ABDM OPD Record Header)
        composition_id = f"comp-{patient.patient_id}"
        entries.append({
            "fullUrl": f"urn:uuid:{composition_id}",
            "resource": {
                "resourceType": "Composition",
                "id": composition_id,
                "status": "final",
                "type": {
                    "coding": [{
                        "system": "https://nrces.in/ndhm/fhir/r4/CodeSystem/ndhm-composition-types",
                        "code": "OPConsultationRecord",
                        "display": "OP Consultation Record"
                    }]
                },
                "subject": {"reference": f"urn:uuid:pat-{patient.patient_id}", "display": patient.name},
                "date": now_iso,
                "author": [{"display": consultation.doctor_name if consultation else "MediKiosk Clinical Intake System"}],
                "title": "Outpatient Clinical Intake & History Record",
                "section": [
                    {
                        "title": "Chief Complaint & History of Present Illness",
                        "code": {"coding": [{"system": "http://snomed.info/sct", "code": "422843007", "display": "Chief complaint"}]},
                        "text": {"status": "generated", "div": f"<div><p><b>Complaint:</b> {summary.chief_complaint}</p><p><b>HPI:</b> {summary.history_of_present_illness}</p></div>"}
                    },
                    {
                        "title": "Medications & Prior Prescriptions",
                        "code": {"coding": [{"system": "http://snomed.info/sct", "code": "721912009", "display": "Medication summary"}]},
                        "text": {"status": "generated", "div": f"<div><p>{len(summary.current_medications)} active medications digitized from previous prescriptions.</p></div>"}
                    }
                ]
            }
        })

        # 2. Patient Resource
        entries.append({
            "fullUrl": f"urn:uuid:pat-{patient.patient_id}",
            "resource": {
                "resourceType": "Patient",
                "id": f"pat-{patient.patient_id}",
                "identifier": [
                    {
                        "system": "https://healthid.abdm.gov.in",
                        "value": patient.abha_id or f"{patient.patient_id}@abdm"
                    },
                    {
                        "system": "https://hospital.gov.in/mrn",
                        "value": patient.patient_id
                    }
                ],
                "name": [{"text": patient.name}],
                "telecom": [{"system": "phone", "value": patient.phone}],
                "gender": patient.gender.lower(),
                "birthDate": f"{datetime.now().year - patient.age}-01-01"
            }
        })

        # 3. Encounter Resource
        entries.append({
            "fullUrl": f"urn:uuid:enc-{patient.patient_id}",
            "resource": {
                "resourceType": "Encounter",
                "id": f"enc-{patient.patient_id}",
                "status": "arrived",
                "class": {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "AMB",
                    "display": "ambulatory (OPD)"
                },
                "subject": {"reference": f"urn:uuid:pat-{patient.patient_id}"},
                "period": {"start": now_iso}
            }
        })

        # 4. Condition Resources (Primary Complaint + Diagnoses)
        for idx, icd in enumerate(summary.icd10_suggestions):
            cond_id = f"cond-{patient.patient_id}-{idx}"
            entries.append({
                "fullUrl": f"urn:uuid:{cond_id}",
                "resource": {
                    "resourceType": "Condition",
                    "id": cond_id,
                    "clinicalStatus": {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
                    },
                    "code": {
                        "coding": [
                            {"system": "http://hl7.org/fhir/sid/icd-10", "code": icd["code"], "display": icd["title"]}
                        ],
                        "text": summary.chief_complaint
                    },
                    "subject": {"reference": f"urn:uuid:pat-{patient.patient_id}"}
                }
            })

        # 5. MedicationStatement Resources
        for idx, med in enumerate(summary.current_medications):
            med_id = f"med-{patient.patient_id}-{idx}"
            entries.append({
                "fullUrl": f"urn:uuid:{med_id}",
                "resource": {
                    "resourceType": "MedicationStatement",
                    "id": med_id,
                    "status": "active",
                    "medicationCodeableConcept": {
                        "text": f"{med.drug_name} {med.strength or ''}"
                    },
                    "subject": {"reference": f"urn:uuid:pat-{patient.patient_id}"},
                    "dosage": [{
                        "text": f"Dose: {med.dosage_frequency} | Timing: {med.timing} | Form: {med.dosage_form}"
                    }]
                }
            })

        # 6. Observation Resources (Extracted Labs)
        for idx, lab in enumerate(summary.investigation_summary):
            obs_id = f"obs-{patient.patient_id}-{idx}"
            entries.append({
                "fullUrl": f"urn:uuid:{obs_id}",
                "resource": {
                    "resourceType": "Observation",
                    "id": obs_id,
                    "status": "final",
                    "code": {
                        "text": lab.test_name
                    },
                    "subject": {"reference": f"urn:uuid:pat-{patient.patient_id}"},
                    "valueQuantity": {
                        "value": float(lab.measured_value) if lab.measured_value.replace('.','',1).isdigit() else lab.measured_value,
                        "unit": lab.unit
                    },
                    "interpretation": [{
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                            "code": "H" if lab.is_abnormal else "N",
                            "display": lab.flag or "Normal"
                        }]
                    }],
                    "referenceRange": [{
                        "text": lab.reference_range
                    }]
                }
            })

        # Final ABDM Bundle structure
        return {
            "resourceType": "Bundle",
            "id": bundle_id,
            "meta": {
                "versionId": "1",
                "lastUpdated": now_iso,
                "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/DocumentBundle"]
            },
            "identifier": {
                "system": "https://abdm.gov.in/fhir/bundles",
                "value": bundle_id
            },
            "type": "document",
            "timestamp": now_iso,
            "entry": entries
        }

abdm_fhir_builder = ABDMFHIRBuilder()
