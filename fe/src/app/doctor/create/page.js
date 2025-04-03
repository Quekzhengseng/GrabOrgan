"use client";

import Link from "next/link";
import { useState } from "react";
import { Loader2, ArrowLeft } from "lucide-react";
import { requestNewOrgans } from "@/utils/recipientUtils";
import { Plus, Trash2 } from "lucide-react";

export default function CreateRecipient() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState(null); // "success" | "error" | null
  const [formData, setFormData] = useState({
    recipient: {
      firstName: "Isaiah",
      lastName: "Chia",
      dateOfBirth: "2001-10-12",
      nric: "T1234567K",
      email: "isaiah@gmail.com",
      address: "31 Victoria St",
      bloodType: "O+",
      gender: "Male",
      organsNeeded: ["heart", "kidneys"], // comma-separated string; will convert to array
      medicalHistory: [
        {
          condition: "Scoliosis",
          dateDiagnosed: "2018-05-12",
          description:
            "Double scoliosis with bends at the mid back and lower back",
          treatment: "Physiotherapy",
        },
      ],
      allergies: ["penicillin", "nuts"], // comma-separated string; will convert to array
      nokContact: {
        firstName: "Sophia",
        lastName: "Chia",
        phone: "88882222",
        relationship: "Sibling",
      },
    },
    labInfo: {
      testType: "Tissue",
      dateOfReport: "2022-03-04",
      reportName: "Tissue Lab Test Report",
      reportUrl:
        "https://www.parkwaylabs.com.sg/docs/parkwaylablibraries/test-catalogues/pls-tissue-forms.pdf?sfvrsn=1418faf5_1",
      comments: "To be reviewed",
    },
  });

  // Generic change handler for top-level fields
  const handleChange = (e, section, field, subfield) => {
    const value = e.target.value;
    setFormData((prev) => {
      const updated = { ...prev };
      if (subfield) {
        updated[section][field] = {
          ...prev[section][field],
          [subfield]: value,
        };
      } else {
        updated[section][field] = value;
      }
      return updated;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus(null); // reset any previous status
    // console.log(formData);

    // const payload = {
    //   data: {
    //     recipient: formData.recipient,
    //     labInfo: {
    //       testType: formData.labInfo.testType,
    //       dateOfReport: formData.labInfo.dateOfReport,
    //       report: {
    //         name: formData.labInfo.reportName,
    //         url: formData.labInfo.reportUrl,
    //       },
    //       hlaTyping: {},
    //       comments: formData.labInfo.comments,
    //     },
    //   },
    // };

    // console.log("Final Payload:", JSON.stringify(payload, null, 2));
    try {
      const response = await requestNewOrgans(formData);

      if (response && response.code >= 200 && response.code < 300) {
        setSubmitStatus("success");
        // Optionally refresh or reset form:
        // window.location.reload();
      } else {
        setSubmitStatus("error");
      }
    } catch (err) {
      console.error(err);
      setSubmitStatus("error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Green Header */}
      <div className="px-6 py-5 flex items-center">
        <Link
          href="/doctor"
          className="flex items-center text-green-600 hover:text-green-800 mb-6 transition-colors"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          <span>Back to Dashboard</span>
        </Link>
      </div>
      {/* Page Body */}
      <div className="max-w-5xl mx-auto px-6 py-8">
        <h1 className="text-3xl font-bold mb-6">Create Recipient</h1>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Recipient Information */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-2xl font-semibold mb-4">
              Recipient Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* First Name */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  First Name
                </label>
                <input
                  type="text"
                  value={formData.recipient.firstName}
                  onChange={(e) => handleChange(e, "recipient", "firstName")}
                  className="w-full border rounded p-2"
                />
              </div>
              {/* Last Name */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  value={formData.recipient.lastName}
                  onChange={(e) => handleChange(e, "recipient", "lastName")}
                  className="w-full border rounded p-2"
                />
              </div>
              {/* Date of Birth */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  Date of Birth
                </label>
                <input
                  type="date"
                  value={formData.recipient.dateOfBirth}
                  onChange={(e) => handleChange(e, "recipient", "dateOfBirth")}
                  className="w-full border rounded p-2"
                />
              </div>
              {/* NRIC */}
              <div>
                <label className="block text-sm font-medium mb-1">NRIC</label>
                <input
                  type="text"
                  value={formData.recipient.nric}
                  onChange={(e) => handleChange(e, "recipient", "nric")}
                  className="w-full border rounded p-2"
                />
              </div>
              {/* Email */}
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  value={formData.recipient.email}
                  onChange={(e) => handleChange(e, "recipient", "email")}
                  className="w-full border rounded p-2"
                />
              </div>
              {/* Address */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  Address
                </label>
                <input
                  type="text"
                  value={formData.recipient.address}
                  onChange={(e) => handleChange(e, "recipient", "address")}
                  className="w-full border rounded p-2"
                />
              </div>
              {/* Blood Type */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  Blood Type
                </label>
                <input
                  type="text"
                  value={formData.recipient.bloodType}
                  onChange={(e) => handleChange(e, "recipient", "bloodType")}
                  className="w-full border rounded p-2"
                />
              </div>
              {/* Gender */}
              <div>
                <label className="block text-sm font-medium mb-1">Gender</label>
                <select
                  value={formData.recipient.gender}
                  onChange={(e) => handleChange(e, "recipient", "gender")}
                  className="w-full border rounded p-2"
                >
                  <option value="">Select Gender</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              {/* Organs Needed */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">
                  Organs Needed
                </label>
                <div className="flex flex-wrap items-center gap-2 border rounded p-2">
                  {formData.recipient.organsNeeded.map((organ, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800"
                    >
                      {organ}
                      <button
                        type="button"
                        className="ml-2 text-gray-600 hover:text-red-600"
                        onClick={() => {
                          const updated = [...formData.recipient.organsNeeded];
                          updated.splice(index, 1);
                          setFormData((prev) => ({
                            ...prev,
                            recipient: {
                              ...prev.recipient,
                              organsNeeded: updated,
                            },
                          }));
                        }}
                      >
                        &times;
                      </button>
                    </span>
                  ))}
                  <input
                    type="text"
                    className="flex-1 min-w-[100px] border-none focus:outline-none"
                    placeholder="Type and press Enter"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        const value = e.target.value.trim();
                        if (
                          value &&
                          !formData.recipient.organsNeeded.includes(value)
                        ) {
                          setFormData((prev) => ({
                            ...prev,
                            recipient: {
                              ...prev.recipient,
                              organsNeeded: [
                                ...prev.recipient.organsNeeded,
                                value,
                              ],
                            },
                          }));
                          e.target.value = "";
                        }
                      }
                    }}
                  />
                </div>
              </div>
              {/* Allergies */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">
                  Allergies
                </label>

                <div className="flex flex-wrap items-center gap-2 border rounded p-2">
                  {formData.recipient.allergies.map((allergy, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800"
                    >
                      {allergy}
                      <button
                        type="button"
                        className="ml-2 text-gray-600 hover:text-red-600"
                        onClick={() => {
                          const updated = [...formData.recipient.allergies];
                          updated.splice(index, 1);
                          setFormData((prev) => ({
                            ...prev,
                            recipient: {
                              ...prev.recipient,
                              allergies: updated,
                            },
                          }));
                        }}
                      >
                        &times;
                      </button>
                    </span>
                  ))}
                  <input
                    type="text"
                    className="flex-1 min-w-[100px] border-none focus:outline-none"
                    placeholder="Type and press Enter"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        const value = e.target.value.trim();
                        if (
                          value &&
                          !formData.recipient.allergies.includes(value)
                        ) {
                          setFormData((prev) => ({
                            ...prev,
                            recipient: {
                              ...prev.recipient,
                              allergies: [...prev.recipient.allergies, value],
                            },
                          }));
                          e.target.value = "";
                        }
                      }
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Medical History */}
            <div className="mt-6">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-xl font-semibold">Medical History</h3>
                <button
                  type="button"
                  onClick={() => {
                    setFormData((prev) => ({
                      ...prev,
                      recipient: {
                        ...prev.recipient,
                        medicalHistory: [
                          ...prev.recipient.medicalHistory,
                          {
                            condition: "",
                            dateDiagnosed: "",
                            description: "",
                            treatment: "",
                          },
                        ],
                      },
                    }));
                  }}
                  className="text-green-600 hover:text-green-800"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>

              {formData.recipient.medicalHistory.map((entry, index) => (
                <div
                  key={index}
                  className="mb-6 border rounded-md p-4 bg-white relative"
                >
                  <button
                    type="button"
                    onClick={() => {
                      const updated = [...formData.recipient.medicalHistory];
                      updated.splice(index, 1);
                      setFormData((prev) => ({
                        ...prev,
                        recipient: {
                          ...prev.recipient,
                          medicalHistory: updated,
                        },
                      }));
                    }}
                    className="absolute top-2 right-2 text-red-500 hover:text-red-700"
                    title="Delete this record"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">
                        Condition
                      </label>
                      <input
                        type="text"
                        value={entry.condition}
                        onChange={(e) => {
                          const updated = [
                            ...formData.recipient.medicalHistory,
                          ];
                          updated[index].condition = e.target.value;
                          setFormData((prev) => ({
                            ...prev,
                            recipient: {
                              ...prev.recipient,
                              medicalHistory: updated,
                            },
                          }));
                        }}
                        className="w-full border rounded p-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">
                        Date Diagnosed
                      </label>
                      <input
                        type="date"
                        value={entry.dateDiagnosed}
                        onChange={(e) => {
                          const updated = [
                            ...formData.recipient.medicalHistory,
                          ];
                          updated[index].dateDiagnosed = e.target.value;
                          setFormData((prev) => ({
                            ...prev,
                            recipient: {
                              ...prev.recipient,
                              medicalHistory: updated,
                            },
                          }));
                        }}
                        className="w-full border rounded p-2"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium mb-1">
                        Description
                      </label>
                      <textarea
                        value={entry.description}
                        onChange={(e) => {
                          const updated = [
                            ...formData.recipient.medicalHistory,
                          ];
                          updated[index].description = e.target.value;
                          setFormData((prev) => ({
                            ...prev,
                            recipient: {
                              ...prev.recipient,
                              medicalHistory: updated,
                            },
                          }));
                        }}
                        className="w-full border rounded p-2"
                        rows={3}
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium mb-1">
                        Treatment
                      </label>
                      <textarea
                        value={entry.treatment}
                        onChange={(e) => {
                          const updated = [
                            ...formData.recipient.medicalHistory,
                          ];
                          updated[index].treatment = e.target.value;
                          setFormData((prev) => ({
                            ...prev,
                            recipient: {
                              ...prev.recipient,
                              medicalHistory: updated,
                            },
                          }));
                        }}
                        className="w-full border rounded p-2"
                        rows={2}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Emergency Contact */}
            <div className="mt-6">
              <h3 className="text-xl font-semibold mb-2">Emergency Contact</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* NOK First Name */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    First Name
                  </label>
                  <input
                    type="text"
                    value={formData.recipient.nokContact.firstName}
                    onChange={(e) =>
                      handleChange(e, "recipient", "nokContact", "firstName")
                    }
                    className="w-full border rounded p-2"
                  />
                </div>
                {/* NOK Last Name */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Last Name
                  </label>
                  <input
                    type="text"
                    value={formData.recipient.nokContact.lastName}
                    onChange={(e) =>
                      handleChange(e, "recipient", "nokContact", "lastName")
                    }
                    className="w-full border rounded p-2"
                  />
                </div>
                {/* NOK Phone */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Phone
                  </label>
                  <input
                    type="text"
                    value={formData.recipient.nokContact.phone}
                    onChange={(e) =>
                      handleChange(e, "recipient", "nokContact", "phone")
                    }
                    className="w-full border rounded p-2"
                  />
                </div>
                {/* NOK Relationship */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Relationship
                  </label>
                  <input
                    type="text"
                    value={formData.recipient.nokContact.relationship}
                    onChange={(e) =>
                      handleChange(e, "recipient", "nokContact", "relationship")
                    }
                    className="w-full border rounded p-2"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Lab Information */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-2xl font-semibold mb-4">Lab Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Test Type */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  Test Type
                </label>
                <input
                  type="text"
                  value={formData.labInfo.testType}
                  onChange={(e) => handleChange(e, "labInfo", "testType")}
                  className="w-full border rounded p-2"
                />
              </div>
              {/* Date of Report */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  Date of Report
                </label>
                <input
                  type="date"
                  value={formData.labInfo.dateOfReport}
                  onChange={(e) => handleChange(e, "labInfo", "dateOfReport")}
                  className="w-full border rounded p-2"
                />
              </div>
              {/* Report Name */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">
                  Report Name
                </label>
                <input
                  type="text"
                  value={formData.labInfo.reportName}
                  onChange={(e) => handleChange(e, "labInfo", "reportName")}
                  className="w-full border rounded p-2"
                />
              </div>
              {/* Report URL */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">
                  Report URL
                </label>
                <input
                  type="url"
                  value={formData.labInfo.reportUrl}
                  onChange={(e) => handleChange(e, "labInfo", "reportUrl")}
                  className="w-full border rounded p-2"
                />
              </div>
              {/* Comments */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">
                  Comments
                </label>
                <textarea
                  value={formData.labInfo.comments}
                  onChange={(e) => handleChange(e, "labInfo", "comments")}
                  className="w-full border rounded p-2"
                  rows={3}
                />
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end space-y-2">
            {submitStatus === "success" && (
              <p className="text-green-600 font-medium">
                Recipient created successfully!
              </p>
            )}
            {submitStatus === "error" && (
              <p className="text-red-600 font-medium">
                Error creating recipient.
              </p>
            )}

            <button
              type="submit"
              className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 flex items-center"
              disabled={isSubmitting}
            >
              {isSubmitting && (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              )}
              {isSubmitting ? "Creating..." : "Create Recipient"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
