class Organ:
    def __init__(
        self, organ_id, donor_id, organ_type, retrieval_datetime, expiry_datetime,
        status, condition, blood_type, weight_grams, hla_typing, histopathology,
        storage_temp_celsius, preservation_solution, notes
    ):
        self.organ_id = organ_id
        self.donor_id = donor_id
        self.organ_type = organ_type
        self.retrieval_datetime = retrieval_datetime
        self.expiry_datetime = expiry_datetime
        self.status = status
        self.condition = condition
        self.blood_type = blood_type
        self.weight_grams = weight_grams
        self.hla_typing = hla_typing
        self.histopathology = histopathology
        self.storage_temp_celsius = storage_temp_celsius
        self.preservation_solution = preservation_solution
        self.notes = notes

    def to_dict(self):
        return {
            "organId": self.organ_id,
            "donorId": self.donor_id,
            "organType": self.organ_type,
            "retrievalDatetime": self.retrieval_datetime,
            "expiryDatetime": self.expiry_datetime,
            "status": self.status,
            "condition": self.condition,
            "bloodType": self.blood_type,
            "weightGrams": self.weight_grams,
            "hlaTyping": self.hla_typing,
            "histopathology": self.histopathology,
            "storageTempCelsius": self.storage_temp_celsius,
            "preservationSolution": self.preservation_solution,
            "notes": self.notes,
        }
