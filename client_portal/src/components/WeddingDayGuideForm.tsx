'use client';

import React, { useState, useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';

interface FormData {
  event_date: string;
  primary_contact: string;
  primary_email: string;
  primary_phone: string;
  partner_contact: string;
  partner_email: string;
  partner_phone: string;
  dressing_location: string;
  dressing_start_time: string;
  dressing_address: string;
  ceremony_site: string;
  ceremony_start: string;
  ceremony_end: string;
  ceremony_address: string;
  ceremony_phone: string;
  reception_site: string;
  reception_start: string;
  dinner_start: string;
  reception_end: string;
  reception_address: string;
  reception_phone: string;
  staff_table: string;
  photo_stop1: string;
  photo_stop2: string;
  photo_stop3: string;
  photo_stop4: string;
  photographer2_start_location: string;
  photographer2_start_location_address: string;
  photographer2_start: string;
  p1_parent_names: string;
  p1_sibling_names: string;
  p1_grandparent_names: string;
  p2_parent_names: string;
  p2_sibling_names: string;
  p2_grandparent_names: string;
  p1_attendant_of_honor: string;
  p2_attendant_of_honor: string;
  flower_attendant_qty: number;
  p1_attendant_qty: number;
  p2_attendant_qty: number;
  ring_bearer_qty: number;
  usher_qty: number;
  additional_photo_request1: string;
  additional_photo_request2: string;
  additional_photo_request3: string;
  additional_photo_request4: string;
  additional_photo_request5: string;
  video_client_names: string;
  wedding_story_song_title: string;
  wedding_story_song_artist: string;
  dance_montage_song_title: string;
  dance_montage_song_artist: string;
  video_special_dances: string;
  photo_booth_text_line1: string;
  photo_booth_text_line2: string;
  photo_booth_placement: string;
  submitted: boolean;
}

interface WeddingDayGuideFormProps {
  contractId: string;
}

const WeddingDayGuideForm: React.FC<WeddingDayGuideFormProps> = ({ contractId }) => {
  const {
    register,
    handleSubmit,
    getValues,
    setValue,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {} as FormData,
    mode: 'onSubmit',
  });

  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formSubmitted, setFormSubmitted] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (contractId) {
      const accessToken = localStorage.getItem('access_token');
      fetch(`https://www.enet2.com/wedding_day_guide/api/wedding_day_guide/${contractId}/`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      })
        .then((response) => response.json())
        .then((data: FormData) => {
          Object.keys(data).forEach((key) => {
            setValue(key as keyof FormData, data[key as keyof FormData], { shouldValidate: false });
          });
          setIsSubmitted(data.submitted || false);
        })
        .catch((error) => console.error('Fetch error:', error));
    }
  }, [contractId, setValue]);

  const handleSave = async () => {
    setIsSaving(true);
    setMessage(null);
    const accessToken = localStorage.getItem('access_token');
    const data = getValues();
    const payload = { ...data, contract: contractId, strict_validation: false };

    try {
      const response = await fetch(
        `https://www.enet2.com/wedding_day_guide/api/wedding_day_guide/${contractId}/`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        }
      );

      if (response.ok) {
        setMessage('Form saved successfully.');
      } else {
        const errorData = await response.json();
        setMessage(errorData?.detail || 'Failed to save form.');
      }
    } catch (error) {
      console.error('Error saving form:', error);
      setMessage('An error occurred while saving the form.');
    } finally {
      setIsSaving(false);
    }
  };

  const onSubmit: SubmitHandler<FormData> = async (data) => {
    setIsSubmitting(true);
    setMessage(null);
    const accessToken = localStorage.getItem('access_token');
    const payload = { ...data, contract: contractId, strict_validation: true, submit: true };

    try {
      const response = await fetch(
        `https://www.enet2.com/wedding_day_guide/api/wedding_day_guide/${contractId}/`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        }
      );

      if (response.ok) {
        setFormSubmitted(true);
        setIsSubmitted(true);
        setMessage('Form submitted successfully.');
      } else {
        setMessage('Failed to submit form. Please try again.');
      }
    } catch (error) {
      setMessage('An error occurred while submitting the form.');
      console.error('Error submitting form:', error);
    } finally {
      setIsSubmitting(false);
    }
  };


return (
    <div className="bg-pistachio min-h-screen flex items-center justify-center py-8">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-6xl w-full">
        {isSubmitted ? (
          <div className="text-center p-4 mb-6 bg-gray-100 rounded-lg">
            <h2 className="font-bold text-lg">Wedding Day Guide Submitted</h2>
            <p>This guide has already been submitted and cannot be modified.</p>
          </div>
        ) : (
          <>
            <h1 className="text-2xl font-bold mb-6 text-center">Wedding Day Guide</h1>
            <div className="text-center p-4 mb-6 bg-gray-100 rounded-lg">
              <h2 className="font-bold text-lg">Emergency Contact</h2>
              <p>(847) 780-7092: Contact Essence with this number in case of any emergency on your wedding day.</p>
            </div>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 bg-gray-100 rounded-lg">
                {/* General Info on the left */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Wedding Date:</label>
                  <input
                    type="date"
                    {...register("event_date", { required: "Wedding Date is required" })}
                    className="border p-2 rounded-lg w-full"
                  />

                  <label className="block text-sm font-medium text-gray-700">Partner 1:</label>
                  <input
                    type="text"
                    {...register("primary_contact", { required: "Partner 1 name is required" })}
                    className="border p-2 rounded-lg w-full"
                  />

                  <label className="block text-sm font-medium text-gray-700">Primary Email:</label>
                  <input
                    type="email"
                    {...register("primary_email", { required: "Primary email is required" })}
                    className="border p-2 rounded-lg w-full"
                  />

                  <label className="block text-sm font-medium text-gray-700">Primary Cell #:</label>
                  <input
                    type="tel"
                    {...register("primary_phone", { required: "Primary cell number is required" })}
                    className="border p-2 rounded-lg w-full"
                  />
                </div>

                {/* Partner Info on the right */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Partner 2:</label>
                  <input
                    type="text"
                    {...register("partner_contact", { required: "Partner 2 name is required" })}
                    className="border p-2 rounded-lg w-full"
                  />

                  <label className="block text-sm font-medium text-gray-700">Partner Email:</label>
                  <input
                    type="email"
                    {...register("partner_email", { required: "Partner email is required" })}
                    className="border p-2 rounded-lg w-full"
                  />

                  <label className="block text-sm font-medium text-gray-700">Partner Cell #:</label>
                  <input
                    type="tel"
                    {...register("partner_phone", { required: "Partner cell number is required" })}
                    className="border p-2 rounded-lg w-full"
                  />
                </div>
              </div>
              <div className="p-4 bg-gray-100 rounded-lg mb-6">
                <h2 className="font-bold text-lg mb-2">For The Lead Photographer</h2>
                <p>The photographer typically comes to the bride&rsquo;s dressing location 3 hours before the ceremony.</p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Dressing Location:</label>
                    <input
                        type="text"
                        {...register("dressing_location", {required: "Dressing location is required"})}
                        className="border p-2 rounded-lg w-full"
                    />
                    <label className="block text-sm font-medium text-gray-700">Start Time:</label>
                    <input
                        type="time"
                        {...register("dressing_start_time", {
                          required: "Start time is required",
                          validate: (value) =>
                              value?.length >= 4 || "Please select a complete time using the time picker"
                        })}
                        className="border p-2 rounded-lg w-full"
                    />
                    {errors.dressing_start_time && (
                        <p className="text-red-500 text-sm mt-1">{errors.dressing_start_time.message}</p>
                    )}
                    <small className="text-gray-500">Be sure to include hours and AM or PM.</small>


                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Dressing Address:</label>
                    <input
                      type="text"
                      {...register("dressing_address", { required: "Dressing address is required" })}
                      className="border p-2 rounded-lg w-full"
                    />
                  </div>
                </div>
              </div>

              {/* Ceremony Location Section */}
              <div className="p-4 bg-gray-100 rounded-lg mb-6">
                <h2 className="font-bold text-lg mb-2">Ceremony Location</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Ceremony Location:</label>
                    <input
                        type="text"
                        {...register("ceremony_site", {required: "Ceremony location is required"})}
                        className="border p-2 rounded-lg w-full"
                    />
                    <label className="block text-sm font-medium text-gray-700">Ceremony Times:</label>

                    <input
                        type="time"
                        {...register("ceremony_start", {
                          required: "Ceremony start time is required",
                          validate: (value) =>
                              value?.length >= 4 || "Please select a complete time using the time picker",
                        })}
                        className="border p-2 rounded-lg w-full"
                    />
                    {errors.ceremony_start && (
                        <p className="text-red-500 text-sm mt-1">{errors.ceremony_start.message}</p>
                    )}
                    <small className="text-gray-500">Be sure to include hours and AM or PM.</small>

                    <span className="block text-center my-1">to</span>

                    <input
                        type="time"
                        {...register("ceremony_end", {
                          required: "Ceremony end time is required",
                          validate: (value) =>
                              value?.length >= 4 || "Please select a complete time using the time picker",
                        })}
                        className="border p-2 rounded-lg w-full"
                    />
                    {errors.ceremony_end && (
                        <p className="text-red-500 text-sm mt-1">{errors.ceremony_end.message}</p>
                    )}
                    <small className="text-gray-500">Be sure to include hours and AM or PM.</small>


                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Ceremony Address:</label>
                    <input
                      type="text"
                      {...register("ceremony_address", { required: "Ceremony address is required" })}
                      className="border p-2 rounded-lg w-full"
                    />

                    <label className="block text-sm font-medium text-gray-700">Ceremony Phone #:</label>
                    <input
                      type="tel"
                      {...register("ceremony_phone", { required: "Ceremony phone number is required" })}
                      className="border p-2 rounded-lg w-full"
                    />
                  </div>
                </div>
              </div>

              {/* Reception Location Section */}
              <div className="p-4 bg-gray-100 rounded-lg">
                <h2 className="font-bold text-lg mb-2">Reception Location</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Reception Location:</label>
                    <input
                      type="text"
                      {...register("reception_site", { required: "Reception location is required" })}
                      className="border p-2 rounded-lg w-full"
                    />

                    <label className="block text-sm font-medium text-gray-700">Cocktail Start Time:</label>
                    <input
                      type="time"
                      {...register("reception_start", {
                        required: "Cocktail start time is required",
                        validate: (value) =>
                          value?.length >= 4 || "Please select a complete time using the time picker"
                      })}
                      className="border p-2 rounded-lg w-full"
                    />
                    {errors.reception_start && (
                      <p className="text-red-500 text-sm mt-1">{errors.reception_start.message}</p>
                    )}
                    <small className="text-gray-500">Be sure to include hours and AM or PM.</small>


                    <label className="block text-sm font-medium text-gray-700">Reception Phone #:</label>
                    <input
                      type="tel"
                      {...register("reception_phone", { required: "Reception phone number is required" })}
                      className="border p-2 rounded-lg w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Reception Address:</label>
                    <input
                        type="text"
                        {...register("reception_address", {required: "Reception address is required"})}
                        className="border p-2 rounded-lg w-full"
                    />

                    <label className="block text-sm font-medium text-gray-700">Dinner Start Time:</label>
                    <input
                        type="time"
                        {...register("dinner_start", {
                          required: "Dinner start time is required",
                          validate: (value) =>
                              value?.length >= 4 || "Please enter a full time including AM or PM"
                        })}
                        className="border p-2 rounded-lg w-full"
                    />
                    {errors.dinner_start && (
                        <p className="text-red-500 text-sm mt-1">{errors.dinner_start.message}</p>
                    )}
                    <small className="text-gray-500">Be sure to include hours and AM or PM.</small>

                    <label className="block text-sm font-medium text-gray-700">Reception Ends:</label>
                    <input
                        type="time"
                        {...register("reception_end", {
                          required: "Reception end time is required",
                          validate: (value) =>
                              value?.length >= 4 || "Please enter a full time including AM or PM"
                        })}
                        className="border p-2 rounded-lg w-full"
                    />
                    {errors.reception_end && (
                        <p className="text-red-500 text-sm mt-1">{errors.reception_end.message}</p>
                    )}
                    <small className="text-gray-500">Be sure to include hours and AM or PM.</small>


                    <p>It is recommended that you seat your photographer/videographer in the room for dinner so that we
                      don&rsquo;t miss anything</p>
                    <label className="block text-sm font-medium text-gray-700">Table #:</label>
                    <input
                        type="text"
                        {...register("staff_table")} // Not required
                        className="border p-2 rounded-lg w-full"
                    />
                  </div>
                </div>
              </div>

              {/* Location Photo Stops Section */}
              <div className="p-4 bg-gray-100 rounded-lg mb-6">
                <h2 className="font-bold text-lg mb-2">Location Photo Stops</h2>
                <p>It is recommended that you only have 1-2 photo location stops, and that you accurately factor in
                  transportation time.</p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Stop 1:</label>
                    <input type="text" {...register("photo_stop1")} className="border p-2 rounded-lg w-full"/>

                    <label className="block text-sm font-medium text-gray-700">Stop 3:</label>
                    <input type="text" {...register("photo_stop3")} className="border p-2 rounded-lg w-full"/>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Stop 2:</label>
                    <input type="text" {...register("photo_stop2")} className="border p-2 rounded-lg w-full"/>

                    <label className="block text-sm font-medium text-gray-700">Stop 4:</label>
                    <input type="text" {...register("photo_stop4")} className="border p-2 rounded-lg w-full"/>
                  </div>
                </div>
              </div>

              {/* For The 2nd Photographer Section */}
              <div className="p-4 bg-gray-100 rounded-lg">
                <h2 className="font-bold text-lg mb-2">For The 2nd Photographer (If Booked)</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Starting Location:</label>
                    <input type="text" {...register("photographer2_start_location")}
                           className="border p-2 rounded-lg w-full"/>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Starting Location Address:</label>
                    <input type="text" {...register("photographer2_start_location_address")}
                           className="border p-2 rounded-lg w-full"/>

                    <label className="block text-sm font-medium text-gray-700">Starting Time:</label>
                    <input type="time" {...register("photographer2_start")} className="border p-2 rounded-lg w-full"/>
                  </div>
                </div>
              </div>
              {/* Shot List Section with Two Columns */}
              <div className="p-4 bg-gray-100 rounded-lg mb-6">
                <h2 className="font-bold text-lg mb-2">Shot List</h2>
                <p>What follows are the photos Essence photographers take at a typical wedding depending on time and
                  organization. Additional photo requests can be added in the next section.</p>
                <div className="grid grid-cols-2 gap-4">
                  {/* Left Column */}
                  <div>
                    {/* Partner 1 Details */}
                    <div className="mb-4">
                      <h3 className="font-semibold mb-2">Dressing Details</h3>
                      <ul className="list-disc pl-5">
                        <li>Dress/Suit</li>
                        <li>Shoes</li>
                        <li>Bouquet/Boutonniere</li>
                        <li>Putting Dress On or Fixing Tie</li>
                      </ul>
                    </div>


                    {/* On Location */}
                    <div className="mb-4">
                      <h3 className="font-semibold mb-2">On Location</h3>
                      <ul className="list-disc pl-5">
                        <li>Partner 1 Alone</li>
                        <li>Partner 2 Alone</li>
                        <li>P1 w/ P2 Attendants</li>
                        <li>P2 w/ P1 Attendants</li>
                        <li>Couple Photos</li>
                        <li>Fun Wedding Party Photos</li>
                      </ul>
                    </div>
                    {/* Before Ceremony (P1) */}
                    <div className="mb-4">
                      <h3 className="font-semibold mb-2">Before Ceremony - Partner 1 (P1)</h3>
                      <ul className="list-disc pl-5">
                        <li>Alone</li>
                        <li>P1 w/ Attendants</li>
                        <li>P1 w/ Flower Attendants</li>
                        <li>P1 w/ Mom</li>
                        <li>P1 w/ Dad</li>
                        <li>P1 w/ Mom & Dad</li>
                        <li>P1 w/ Siblings</li>
                        <li>P1 w/ Immediate Family</li>
                      </ul>
                    </div>

                    {/* Before Ceremony (P2) */}
                    <div>
                      <h3 className="font-semibold mb-2">Before Ceremony - Partner 2 (P2)</h3>
                      <ul className="list-disc pl-5">
                        <li>Alone</li>
                        <li>P2 w/ Attendants</li>
                        <li>P2 w/ Ring Bearers</li>
                        <li>P2 w/ Ushers</li>
                        <li>P2 w/ Mom</li>
                        <li>P2 w/ Dad</li>
                        <li>P2 w/ Mom & Dad</li>
                        <li>P2 w/ Siblings</li>
                        <li>P2 w/ Immediate Family</li>
                      </ul>
                    </div>
                  </div>

                  {/* Right Column */}
                  <div>
                    {/* Post-Ceremony */}
                    <div className="mb-4">
                      <h3 className="font-semibold mb-2">Post-Ceremony</h3>
                      <ul className="list-disc pl-5">
                        <li>P1 at Altar</li>
                        <li>P2 at Altar</li>
                        <li>Couple at Altar</li>
                        <li>Couple w/ Wedding Party</li>
                        <li>Couple w/ P1&apos;s Parents</li>
                        <li>Couple w/ P1&apos;s Immediate Family</li>
                        <li>Couple w/ P1&apos;s Grandparents</li>
                        <li>Couple w/ P1&apos;s Extended Family</li>
                        <li>Couple w/ Both Sets of Parents</li>
                        <li>Couple w/ P2&apos;s Parents</li>
                        <li>Couple w/ P2&apos;s Immediate Family</li>
                        <li>Couple w/ P2&apos;s Grandparents</li>
                        <li>Couple w/ P2&apos;s Extended Family</li>
                        <li>Church Exit</li>
                      </ul>
                    </div>

                    {/* Ceremony */}
                    <div className="mb-4">
                      <h3 className="font-semibold mb-2">Ceremony</h3>
                      <ul className="list-disc pl-5">
                        <li>Processional</li>
                        <li>Vows</li>
                        <li>Ring Exchange</li>
                        <li>First Kiss</li>
                        <li>Flowers to Mothers</li>
                        <li>Presentation of Couple</li>
                        <li>Recessional</li>
                      </ul>
                    </div>

                    {/* Reception */}
                    <div>
                      <h3 className="font-semibold mb-2">Reception</h3>
                      <ul className="list-disc pl-5">
                        <li>Reception Details</li>
                        <li>Cocktail Hour Mingling</li>
                        <li>Introductions</li>
                        <li>Cake Cutting</li>
                        <li>Toasts</li>
                        <li>First Dance</li>
                        <li>Special Dances</li>
                        <li>Bouquet Toss</li>
                        <li>Garter Toss</li>
                        <li>General Dancing</li>
                        <li>Goodbye Shot</li>
                      </ul>
                    </div>
                  </div>
                </div>
                <p>Essence does not recommend table shots or backdrop photography with a single photographer. If you require
                  either of these things, please call us to add a second photographer.</p>
              </div>
              {/* Family & Wedding Party Info Section */}
              <div className="p-4 bg-gray-100 rounded-lg">
                <h2 className="font-bold text-lg mb-2">Family & Wedding Party Info</h2>
                <div className="grid grid-cols-2 gap-4">
                  {/* Left Column for Family */}
                  <div>
                    <h3 className="font-semibold mb-2">Family</h3>
                    {/* Bride's Side */}
                    <div className="mb-4">
                      <h4 className="font-semibold">Partner 1&apos;s Side</h4>
                      <label className="block text-sm font-medium text-gray-700">P1&apos;s Parents:</label>
                      <input type="text" {...register("p1_parent_names")} className="border p-2 rounded-lg w-full"/>

                      <label className="block text-sm font-medium text-gray-700">P1&apos;s Siblings:</label>
                      <input type="text" {...register("p1_sibling_names")} className="border p-2 rounded-lg w-full"/>

                      <label className="block text-sm font-medium text-gray-700">P1&apos;s Grandparents:</label>
                      <input type="text" {...register("p1_grandparent_names")}
                             className="border p-2 rounded-lg w-full"/>
                    </div>

                    {/* Groom's Side */}
                    <div>
                      <h4 className="font-semibold">Partner 2&apos;s Side</h4>
                      <label className="block text-sm font-medium text-gray-700">Partner 2&apos;s Parents:</label>
                      <input type="text" {...register("p2_parent_names")} className="border p-2 rounded-lg w-full"/>

                      <label className="block text-sm font-medium text-gray-700">Partner 2&apos;s Siblings:</label>
                      <input type="text" {...register("p2_sibling_names")} className="border p-2 rounded-lg w-full"/>

                      <label className="block text-sm font-medium text-gray-700">Partner 2&apos;s Grandparents:</label>
                      <input type="text" {...register("p2_grandparent_names")}
                             className="border p-2 rounded-lg w-full"/>
                    </div>
                  </div>

                  {/* Right Column for Wedding Party */}
                  <div>
                    <h3 className="font-semibold mb-2">Wedding Party</h3>
                    <label className="block text-sm font-medium text-gray-700">Attendant of Honor P1:</label>
                    <input type="text" {...register("p1_attendant_of_honor")} className="border p-2 rounded-lg w-full"/>

                    <label className="block text-sm font-medium text-gray-700">Attendant of Honor P2:</label>
                    <input type="text" {...register("p2_attendant_of_honor")} className="border p-2 rounded-lg w-full"/>

                    <label className="block text-sm font-medium text-gray-700"># of Attendants P1:</label>
                    <input type="number" {...register("p1_attendant_qty")} className="border p-2 rounded-lg w-full"/>

                    <label className="block text-sm font-medium text-gray-700"># of Attendants P2:</label>
                    <input type="number" {...register("p2_attendant_qty")} className="border p-2 rounded-lg w-full"/>

                    <label className="block text-sm font-medium text-gray-700"># of Flower Attendants:</label>
                    <input type="number" {...register("flower_attendant_qty")} className="border p-2 rounded-lg w-full"/>

                    <label className="block text-sm font-medium text-gray-700"># of Ring Bearers:</label>
                    <input type="number" {...register("ring_bearer_qty")} className="border p-2 rounded-lg w-full"/>

                    <label className="block text-sm font-medium text-gray-700"># of Ushers:</label>
                    <input type="number" {...register("usher_qty")} className="border p-2 rounded-lg w-full"/>
                  </div>
                </div>
              </div>
              {/* Additional Photography Requests Section */}
              <div className="p-4 bg-gray-100 rounded-lg mb-6">
                <h2 className="font-bold text-lg mb-2">Additional Photography Requests</h2>
                <p>Please add your photo requests below. We will do our best to get to all of them, time and weather
                  permitting.</p>
                <p>&nbsp;</p>


                <div className="grid grid-cols-1 gap-4">
                  {/* Single Column for All Photo Requests */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Formal/Posed Photo Requests:</label>
                    <input type="text" {...register("additional_photo_request1")} className="border p-2 rounded-lg w-full"/>

                    <label className="block text-sm font-medium text-gray-700">Formal/Posed Photo Requests (2):</label>
                    <input type="text" {...register("additional_photo_request2")} className="border p-2 rounded-lg w-full"/>

                    <label className="block text-sm font-medium text-gray-700">Formal/Posed Photo Requests (3):</label>
                    <input type="text" {...register("additional_photo_request3")} className="border p-2 rounded-lg w-full"/>

                    <label className="block text-sm font-medium text-gray-700">Other Photo Requests:</label>
                    <input type="text" {...register("additional_photo_request4")} className="border p-2 rounded-lg w-full"/>

                    <label className="block text-sm font-medium text-gray-700">Other Photo Requests (2):</label>
                    <input type="text" {...register("additional_photo_request5")} className="border p-2 rounded-lg w-full"/>
                  </div>
                </div>
              </div>
              {/* Videography Customers Only Section */}
              <div className="p-4 bg-gray-100 rounded-lg mb-6">
                <h2 className="font-bold text-lg mb-2">Videography Customers Only</h2>
                <p>Essence cannot process your video until you have provided us with the following information.</p>
                <p>&nbsp;</p>
                <p>We deliver weddings online through the Vimeo platform. If you would also like your video on a Blu-Ray
                  Disc, they are available for $100 if you contact our office directly, prior to your wedding. Please note:
                  Blu-Ray discs can only be viewed in a Blu-Ray player and are not compatible with standard DVD players or
                  computers. Online videos can be viewed or downloaded on any digital media device, and will be viewable on
                  Vimeo.com for 1 year after they are delivered.</p>
                <p>&nbsp;</p>
                <p>Please type your names below EXACTLY as you would like them to appear in the final video. Traditionally
                  the names are listed as John and Sara Flemming.</p>
                <p>&nbsp;</p>

                <label className="block text-sm font-medium text-gray-700">Names:</label>
                <input type="text" {...register("video_client_names")} className="border p-2 rounded-lg w-full"/>
                <p>&nbsp;</p>


                {/* Wedding Story */}
                <h3 className="font-semibold mb-2">Wedding Story</h3>
                <p>Your wedding story will be a collection of highlights from your full wedding day. Your song selection
                  should be one slow or medium tempo song. We strongly encourage you to pick a song with a length of 3-4
                  minutes, as a shorter song will decrease the amount of footage the editors are able to include in your
                  highlight video. Re-edits of videos due to the choice of a short length song will be charged a fee.</p>
                <p>&nbsp;</p>

                <label className="block text-sm font-medium text-gray-700">WS Song Title:</label>
                <input type="text" {...register("wedding_story_song_title")} className="border p-2 rounded-lg w-full"/>
                <p>&nbsp;</p>

                <label className="block text-sm font-medium text-gray-700">WS Song Artist:</label>
                <input type="text" {...register("wedding_story_song_artist")} className="border p-2 rounded-lg w-full"/>
                <p>&nbsp;</p>


                {/* Dance Montage */}
                <h3 className="font-semibold mb-2">Dance Montage</h3>
                <p>Your dance montage will be an upbeat collection of footage shot during the general dancing portion of
                  your evening paired with one song. Re-edits of videos due to the choice of a short length song will be
                  charged a fee.</p>
                <p>We cannot complete your video without BOTH your Wedding Story and Dance Montage songs.</p>
                <p>&nbsp;</p>

                <label className="block text-sm font-medium text-gray-700">DM Song Title:</label>
                <input type="text" {...register("dance_montage_song_title")} className="border p-2 rounded-lg w-full"/>
                <label className="block text-sm font-medium text-gray-700">DM Song Artist:</label>
                <input type="text" {...register("dance_montage_song_artist")} className="border p-2 rounded-lg w-full"/>
                <p>&nbsp;</p>

                {/* Additional Editing Notes */}
                <h3 className="font-semibold mb-2">Additional Editing Notes</h3>
                <p>Videography customers receive the two above highlight videos as well as other important portions of their
                  day. Videography customers who have not added Bridal Prep / First Look to their video coverage receive the
                  following live footage in their video: Ceremony, Introductions, Cake Cutting, Toasts, First Dance, Special
                  Dances (i.e. Father/Daughter dance and Mother/Son dance), and Bouquet/Garter toss. These portions are only
                  a part of the video if the events occurred and the videographer is present during the time they
                  happen.</p>
                <p>If you are having other “special dances” besides the Mother/Son and Father/Daughter dance, please list
                  them below so that your videographer and editor know to include footage of them in your video.</p>
                <p>&nbsp;</p>

                <label className="block text-sm font-medium text-gray-700">Other Special Dances to be Included:</label>
                <input type="text" {...register("video_special_dances")} className="border p-2 rounded-lg w-full"/>
              </div>
              {/* Photo Booth Customers Only Section */}
              <div className="p-4 bg-gray-100 rounded-lg mb-6">
                <h2 className="font-bold text-lg mb-2">Photo Booth Customers Only</h2>
                <p>Your open-air photo booth, with sparkly, silver backdrop and props, opens during the last 3 hours of the
                  open dance time at your wedding. The booth prints (2) 2x6 photo strips for each set of images. The digital
                  images will be sent to you as well, after the wedding via Google Drive. (Essence does not provide an album
                  for photo strips.)</p>
                <p>&nbsp;</p>

                <p>How would you like your names and wedding date to appear on your photo strip? (ie. Kim and Joe, Joe &
                  Kim, May 22, 2025, or 05/22/25)</p>
                <p>&nbsp;</p>

                <label className="block text-sm font-medium text-gray-700">Text Line 1 (up to 15 characters):</label>
                <input
                  type="text"
                  {...register("photo_booth_text_line1")}
                  maxLength={15} // Ensure maxLength is a number
                  className="border p-2 rounded-lg w-full"
                />

                <label className="block text-sm font-medium text-gray-700">Text Line 2 (up to 15 characters):</label>
                <input
                  type="text"
                  {...register("photo_booth_text_line2")}
                  maxLength={15} // Ensure maxLength is a number
                  className="border p-2 rounded-lg w-full"
                />
                <p>&nbsp;</p>
                <p>
                  Please describe the location in your facility where we will be setting up. Please remember that we will
                  need a 5&apos;x7&apos; space within 15 feet of an outlet, and a skirted high-top table. (Example: You will be in the
                  far corner of the room next to the head table, or you will be in the front, just inside the doors.)
                </p>
                <p>&nbsp;</p>
                <label className="block text-sm font-medium text-gray-700">Placement:</label>
                <input type="text" {...register("photo_booth_placement")} className="border p-2 rounded-lg w-full"/>
              </div>
              {/* Warning Message */}
              <div className="text-red-500 text-center">
                Please note that once you submit this form, you will not be able to make any changes.
              </div>
              {message && (
                <div
                  className={`p-4 mb-6 text-center rounded-lg ${
                    message.includes('successfully') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}
                >
                  {message}
                </div>
              )}
            <div className="flex flex-col space-y-4">
              {/* Save Button */}
              <button
                type="button"
                onClick={handleSave} // Save without validation
                disabled={isSaving}
                className="bg-blue-500 text-white py-2 px-4 rounded"
              >
                {isSaving ? 'Saving...' : 'Save'}
              </button>

              <button
                  type="submit"
                  disabled={isSubmitting || formSubmitted}
                  className="bg-green-500 text-white py-2 px-4 rounded ml-2"
              >
                {isSubmitting ? 'Submitting...' : 'Submit'}
              </button>
            </div>

            </form>
          </>
        )}
      </div>
    </div>
);
};

export default WeddingDayGuideForm;