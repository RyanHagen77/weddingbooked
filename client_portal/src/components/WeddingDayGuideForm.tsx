'use client';

import React, { useState, useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';

import StyledTimePicker from './TimeInput';

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
  photo_booth_end_time: string;
  submitted: boolean;
}

interface WeddingDayGuideFormProps {
  contractId: string;
}

const WeddingDayGuideForm: React.FC<WeddingDayGuideFormProps> = ({ contractId }) => {
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
    getValues,
  } = useForm<FormData>({
    defaultValues: {} as FormData,
    mode: 'onSubmit',
  });

  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formSubmitted, setFormSubmitted] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const inputClass =
    "border p-2 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-pinkbrand bg-white shadow-sm font-sans";

  // Time field states for TimeInput components
  const [dressingStartTimeRaw, setDressingStartTimeRaw] = useState('00:00'); // what Timekeeper uses
  const [ceremonyStartRaw, setCeremonyStartRaw] = useState('00:00');
  const [ceremonyEndRaw, setCeremonyEndRaw] = useState('00:00');
  const [receptionStartTimeRaw, setReceptionStartTimeRaw] = useState('00:00')
  const [dinnerStartTimeRaw, setDinnerStartTimeRaw] = useState('00:00')
  const [receptionEndTimeRaw, setReceptionEndTimeRaw] = useState('00:00');
  const [photographer2StartRaw, setPhotographer2StartRaw] = useState('00:00');
  const [photoBoothEndTimeRaw, setPhotoBoothEndTimeRaw] = useState('00:00'); // 👈 Add here


useEffect(() => {
  if (!contractId) return;

  const accessToken = localStorage.getItem('access_token');

  fetch(`https://weddingbooked.app/wedding_day_guide/api/wedding_day_guide/${contractId}/`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
  })
    .then((response) => response.json())
    .then((data: FormData) => {
      Object.keys(data).forEach((key) => {
        // Ensure the key is valid by narrowing its type to keyof FormData
        const typedKey = key as keyof FormData;
        if (typedKey in data) {
          setValue(typedKey, data[typedKey], { shouldValidate: false });
        }
      });

      if (data.dressing_start_time) {
        const [hourStr, minuteStr] = data.dressing_start_time.split(':');
        const raw = `${hourStr.padStart(2, '0')}:${minuteStr.padStart(2, '0')}`;
        setDressingStartTimeRaw(raw);
        setValue('dressing_start_time', raw, { shouldValidate: false });
      }

      if (data.ceremony_start) {
        const [hourStr, minuteStr] = data.ceremony_start.split(':');
        const raw = `${hourStr.padStart(2, '0')}:${minuteStr.padStart(2, '0')}`;
        setCeremonyStartRaw(raw);
        setValue('ceremony_start', raw, { shouldValidate: false });
      }

      if (data.ceremony_end) {
        const [hourStr, minuteStr] = data.ceremony_end.split(':');
        const raw = `${hourStr.padStart(2, '0')}:${minuteStr.padStart(2, '0')}`;
        setCeremonyEndRaw(raw);
        setValue('ceremony_end', raw, { shouldValidate: false });
      }

      if (data.reception_start) {
        const [hourStr, minuteStr] = data.reception_start.split(':');
        const raw = `${hourStr.padStart(2, '0')}:${minuteStr.padStart(2, '0')}`;
        setReceptionStartTimeRaw(raw);
        setValue('reception_start', raw, { shouldValidate: false });
      }

      if (data.dinner_start) {
        const [hourStr, minuteStr] = data.dinner_start.split(':');
        const raw = `${hourStr.padStart(2, '0')}:${minuteStr.padStart(2, '0')}`;
        setDinnerStartTimeRaw(raw);
        setValue('dinner_start', raw, { shouldValidate: false });
      }

      if (data.reception_end) {
        const [hourStr, minuteStr] = data.reception_end.split(':');
        const raw = `${hourStr.padStart(2, '0')}:${minuteStr.padStart(2, '0')}`;
        setReceptionEndTimeRaw(raw);
        setValue('reception_end', raw, { shouldValidate: false });
      }

      if (data.photographer2_start) {
        const [hourStr, minuteStr] = data.photographer2_start.split(':');
        const raw = `${hourStr.padStart(2, '0')}:${minuteStr.padStart(2, '0')}`;
        setPhotographer2StartRaw(raw);
        setValue('photographer2_start', raw, { shouldValidate: false });
      }

      setIsSubmitted(data.submitted || false);
    })
    .catch((error) => {
      console.error('Error fetching wedding guide:', error);
    });
}, [contractId, setValue]);

useEffect(() => {
  if (Object.keys(errors).length > 0) {
    const firstErrorField = Object.keys(errors)[0];
    const errorElement = document.querySelector(`[name="${firstErrorField}"]`);

    if (errorElement && typeof errorElement.scrollIntoView === 'function') {
      errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      (errorElement as HTMLElement).focus();
    }

    // Create the tooltip popup
    const existingPopup = document.querySelector(`#popup-${firstErrorField}`);
    if (!existingPopup && errorElement) {
      const rect = (errorElement as HTMLElement).getBoundingClientRect();
      const popup = document.createElement('div');
      popup.id = `popup-${firstErrorField}`;
      popup.innerText = 'Oops! We need this. Please fill this out.';
      popup.className = 'absolute z-50 bg-red-100 text-red-700 text-sm px-3 py-1 rounded shadow';
      popup.style.position = 'absolute';
      popup.style.left = `${rect.left}px`;
      popup.style.top = `${rect.top - 30}px`; // slightly above the input
      popup.style.maxWidth = '250px';

      document.body.appendChild(popup);

      // Auto-remove popup after 5 seconds
      setTimeout(() => {
        popup.remove();
      }, 5000);
    }
  }
}, [errors]);



  const handleSave = async () => {
    setIsSaving(true);
    setMessage(null);
    const accessToken = localStorage.getItem('access_token');
    const data = getValues();
    const payload = { ...data, contract: contractId, strict_validation: false };

    try {
      const response = await fetch(
        `https://weddingbooked.app/wedding_day_guide/api/wedding_day_guide/${contractId}/`,
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
  // Handle form submit
  const onSubmit: SubmitHandler<FormData> = async (data) => {
    setIsSubmitting(true);
    setMessage(null);

    const accessToken = localStorage.getItem('access_token');
    const payload = { ...data, contract: contractId, strict_validation: true, submit: true };

    try {
      const response = await fetch(
        `https://weddingbooked.app/wedding_day_guide/api/wedding_day_guide/${contractId}/`,
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
        setFormSubmitted(true); // Ensure this state is set after a successful submission
        setIsSubmitted(true);
        setMessage('Form submitted successfully.');
      } else {
        const errorData = await response.json();
        setMessage(errorData?.detail || 'Failed to submit form. Please check your entries.');
      }
    } catch (error) {
      console.error('Error submitting form:', error);
      setMessage('An error occurred while submitting the form.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Loading screen
  if (isSaving || isSubmitting) {
    return <div>Loading...</div>;
  }



  return (
    <div className="bg-neutral-100 min-h-screen px-4 md:px-12 py-10 md:py-16 text-gray-800 font-sans">
      <div className="max-w-5xl mx-auto">
        {isSubmitted ? (
          <div className="text-center p-6 mb-10 bg-white rounded-lg border border-gray-300 shadow-sm">
            <h2 className="text-xl font-semibold mb-2 text-gray-800">Wedding Day Guide Submitted</h2>
            <p className="text-gray-600">This guide has already been submitted and cannot be modified.</p>
          </div>
        ) : (
          <>
            <h1 className="text-4xl font-bold mb-8 text-center tracking-wide border-b-2 border-pinkbrand pb-4 text-gray-800 font-display">
              Wedding Planning Guide
            </h1>

            <div className="text-center p-6 mb-10 bg-[#fdf4f5] border border-pinkbrand rounded-lg shadow-sm">
              <h2 className="font-bold text-lg text-[#a2585f] mb-2 font-display">Emergency Contact</h2>
              <p className="text-sm text-[#5b2e30]">(847) 780-7092: Contact Essence with this number in case of emergency.</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-10">
              <section className="grid grid-cols-1 md:grid-cols-2 gap-8 bg-[#fdf4f5] p-6 rounded-lg border border-gray-200 shadow-sm">
                <div className="space-y-4">
                  <label className="block text-sm font-medium text-gray-700">Wedding Date</label>
                  <input
                    type="date"
                    {...register("event_date", { required: true })}
                    className={inputClass}
                  />

                  <label className="block text-sm font-medium text-gray-700">Partner 1</label>
                  <input
                    type="text"
                    {...register("primary_contact", { required: true })}
                    className={inputClass}
                  />

                  <label className="block text-sm font-medium text-gray-700">Primary Email</label>
                  <input
                    type="email"
                    {...register("primary_email", { required: true })}
                    className={inputClass}
                  />

                  <label className="block text-sm font-medium text-gray-700">Primary Cell #</label>
                  <input
                    type="tel"
                    {...register("primary_phone", { required: true })}
                    className={inputClass}
                  />
                </div>

                <div className="space-y-4">
                  <label className="block text-sm font-medium text-gray-700">Partner 2</label>
                  <input
                    type="text"
                    {...register("partner_contact", { required: true })}
                    className={inputClass}
                  />

                  <label className="block text-sm font-medium text-gray-700">Partner Email</label>
                  <input
                    type="email"
                    {...register("partner_email", { required: true })}
                    className={inputClass}
                  />

                  <label className="block text-sm font-medium text-gray-700">Partner Cell #</label>
                  <input
                    type="tel"
                    {...register("partner_phone", { required: true })}
                    className={inputClass}
                  />
                </div>
              </section>

              {/* For The Lead Photographer Section */}
              <section className="bg-[#fdf4f5] p-6 rounded-lg border border-pinkbrand shadow-sm">
                <h2 className="text-xl font-bold mb-2 text-pinkbrand border-b border-pinkbrand pb-2 font-display">
                  For The Lead Photographer
                </h2>
                <p className="mb-4 text-sm text-gray-700 font-sans">
                  The photographer typically comes to the bride’s dressing location 3 hours before the ceremony.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <label className="block text-sm font-medium text-gray-700 font-sans">Dressing Location:</label>
                    <input type="text" {...register("dressing_location")} className={inputClass} />

                    <StyledTimePicker
                      label="Start Time"
                      value={dressingStartTimeRaw}
                      onChange={(val) => {
                        setDressingStartTimeRaw(val);
                        setValue("dressing_start_time", val, { shouldValidate: false });
                      }}
                    />
                    <input type="hidden" {...register("dressing_start_time")} />
                  </div>

                  <div className="space-y-4">
                    <label className="block text-sm font-medium text-gray-700 font-sans">Dressing Address:</label>
                    <input type="text" {...register("dressing_address")} className={inputClass} />
                  </div>
                </div>
              </section>

              {/* Ceremony Location Section */}
              <section className="bg-[#fdf4f5] p-6 rounded-lg border border-pinkbrand shadow-sm">
                <h2 className="text-xl font-bold mb-2 text-pinkbrand border-b border-pinkbrand pb-2 font-display">
                  Ceremony Location
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <label className="block text-sm font-medium text-gray-700 font-sans">Ceremony Location:</label>
                    <input type="text" {...register("ceremony_site")} className={inputClass} />

                    <StyledTimePicker
                      label="Ceremony Start"
                      value={ceremonyStartRaw}
                      onChange={(val) => {
                        setCeremonyStartRaw(val);
                        setValue("ceremony_start", val, { shouldValidate: false });
                      }}
                    />
                    <input type="hidden" {...register("ceremony_start")} />

                    <StyledTimePicker
                      label="Ceremony End"
                      value={ceremonyEndRaw}
                      onChange={(val) => {
                        setCeremonyEndRaw(val);
                        setValue("ceremony_end", val, { shouldValidate: false });
                      }}
                    />
                    <input type="hidden" {...register("ceremony_end")} />
                  </div>

                  <div className="space-y-4">
                    <label className="block text-sm font-medium text-gray-700 font-sans">Ceremony Address:</label>
                    <input type="text" {...register("ceremony_address")} className={inputClass} />

                    <label className="block text-sm font-medium text-gray-700 font-sans">Ceremony Phone #:</label>
                    <input type="tel" {...register("ceremony_phone")} className={inputClass} />
                  </div>
                </div>
              </section>

              {/* Reception Location Section */}
              <section className="bg-[#fdf4f5] p-6 rounded-lg border border-pinkbrand shadow-sm">
                <h2 className="text-xl font-bold mb-2 text-pinkbrand border-b border-pinkbrand pb-2 font-display">
                  Reception Location
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <label className="block text-sm font-medium text-gray-700 font-sans">Reception Location:</label>
                    <input type="text" {...register("reception_site")} className={inputClass} />

                    <StyledTimePicker
                      label="Cocktail Start Time"
                      value={receptionStartTimeRaw}
                      onChange={(val) => {
                        setReceptionStartTimeRaw(val);
                        setValue("reception_start", val, { shouldValidate: false });
                      }}
                    />
                    <input type="hidden" {...register("reception_start")} />

                    <label className="block text-sm font-medium text-gray-700 font-sans">Reception Phone #:</label>
                    <input type="tel" {...register("reception_phone")} className={inputClass} />
                  </div>

                  <div className="space-y-4">
                    <label className="block text-sm font-medium text-gray-700 font-sans">Reception Address:</label>
                    <input type="text" {...register("reception_address")} className={inputClass} />

                    <StyledTimePicker
                      label="Dinner Start Time"
                      value={dinnerStartTimeRaw}
                      onChange={(val) => {
                        setDinnerStartTimeRaw(val);
                        setValue("dinner_start", val, { shouldValidate: false });
                      }}
                    />
                    <input type="hidden" {...register("dinner_start")} />

                    <StyledTimePicker
                      label="Reception Ends"
                      value={receptionEndTimeRaw}
                      onChange={(val) => {
                        setReceptionEndTimeRaw(val);
                        setValue("reception_end", val, { shouldValidate: false });
                      }}
                    />
                    <input type="hidden" {...register("reception_end")} />

                    <p className="text-sm italic text-gray-600 mt-2 font-sans">
                      It is recommended that you seat your photographer/videographer in the room for dinner so that we don’t miss anything.
                    </p>

                    <label className="block text-sm font-medium text-gray-700 font-sans mt-4">Table #:</label>
                    <input type="text" {...register("staff_table")} className={inputClass} />
                  </div>
                </div>
              </section>

                {/* Location Photo Stops Section */}
                <section className="bg-[#fdf4f5] p-6 rounded-lg border border-pinkbrand shadow-sm">
                  <h2 className="text-xl font-bold mb-2 text-pinkbrand border-b border-pinkbrand pb-2 font-display">
                    Location Photo Stops
                  </h2>
                  <p className="text-sm text-gray-700 mb-4 font-sans">
                    It is recommended that you only have 1–2 photo location stops, and that you accurately factor in transportation
                    time.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <label className="block text-sm font-medium text-gray-700 font-sans">Stop 1:</label>
                      <input type="text" {...register("photo_stop1")} className={inputClass} />

                      <label className="block text-sm font-medium text-gray-700 font-sans">Stop 3:</label>
                      <input type="text" {...register("photo_stop3")} className={inputClass} />
                    </div>
                    <div className="space-y-4">
                      <label className="block text-sm font-medium text-gray-700 font-sans">Stop 2:</label>
                      <input type="text" {...register("photo_stop2")} className={inputClass} />

                      <label className="block text-sm font-medium text-gray-700 font-sans">Stop 4:</label>
                      <input type="text" {...register("photo_stop4")} className={inputClass} />
                    </div>
                  </div>
                </section>

                <section className="bg-[#fdf4f5] p-6 rounded-lg border border-pinkbrand shadow-sm">
                  <h2 className="text-xl font-bold mb-2 text-pinkbrand border-b border-pinkbrand pb-2 font-display">
                    For The 2nd Photographer (If Booked)
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <label className="block text-sm font-medium text-gray-700 font-sans">Starting Location:</label>
                      <input type="text" {...register("photographer2_start_location")} className={inputClass} />
                    </div>
                    <div className="space-y-4">
                      <label className="block text-sm font-medium text-gray-700 font-sans">Starting Location Address:</label>
                      <input type="text" {...register("photographer2_start_location_address")} className={inputClass} />

                      <StyledTimePicker
                          label="Starting Time (Photographer 2)"
                          value={photographer2StartRaw}
                          onChange={(val) => {
                            setPhotographer2StartRaw(val);
                            setValue("photographer2_start", val, {shouldValidate: false});
                          }}
                      />
                      <input type="hidden" {...register("photographer2_start")} />
                    </div>
                  </div>
                </section>

                {/* Shot List Section with Two Columns */}
                {/* Shot List Section */}
                <section className="p-6 bg-[#fdf4f5] rounded-lg border border-pinkbrand shadow-sm mb-10">
                  <h2 className="text-xl font-bold text-pinkbrand border-b border-pinkbrand pb-2 mb-4 font-display">
                    Shot List
                  </h2>
                  <p className="mb-6 text-sm text-gray-700 font-sans">
                    What follows are the photos Essence photographers take at a typical wedding depending on time and organization.
                    Additional photo requests can be added in the next section.
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Left Column */}
                    <div className="space-y-6">
                      <div>
                        <h3 className="font-semibold text-gray-800 mb-1 font-sans">Dressing Details</h3>
                        <ul className="list-disc pl-5 text-sm text-gray-700 font-sans">
                          <li>Dress/Suit</li>
                          <li>Shoes</li>
                          <li>Bouquet/Boutonniere</li>
                          <li>Putting Dress On or Fixing Tie</li>
                        </ul>
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-800 mb-1 font-sans">On Location</h3>
                        <ul className="list-disc pl-5 text-sm text-gray-700 font-sans">
                          <li>Partner 1 Alone</li>
                          <li>Partner 2 Alone</li>
                          <li>P1 w/ P2 Attendants</li>
                          <li>P2 w/ P1 Attendants</li>
                          <li>Couple Photos</li>
                          <li>Fun Wedding Party Photos</li>
                        </ul>
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-800 mb-1 font-sans">Before Ceremony - Partner 1 (P1)</h3>
                        <ul className="list-disc pl-5 text-sm text-gray-700 font-sans">
                          <li>Alone</li>
                          <li>P1 w/ Attendants</li>
                          <li>P1 w/ Flower Attendants</li>
                          <li>P1 w/ Mom</li>
                          <li>P1 w/ Dad</li>
                          <li>P1 w/ Mom &amp; Dad</li>
                          <li>P1 w/ Siblings</li>
                          <li>P1 w/ Immediate Family</li>
                        </ul>
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-800 mb-1 font-sans">Before Ceremony - Partner 2 (P2)</h3>
                        <ul className="list-disc pl-5 text-sm text-gray-700 font-sans">
                          <li>Alone</li>
                          <li>P2 w/ Attendants</li>
                          <li>P2 w/ Ring Bearers</li>
                          <li>P2 w/ Ushers</li>
                          <li>P2 w/ Mom</li>
                          <li>P2 w/ Dad</li>
                          <li>P2 w/ Mom &amp; Dad</li>
                          <li>P2 w/ Siblings</li>
                          <li>P2 w/ Immediate Family</li>
                        </ul>
                      </div>
                    </div>

                    {/* Right Column */}
                    <div className="space-y-6">
                      <div>
                        <h3 className="font-semibold text-gray-800 mb-1 font-sans">Post-Ceremony</h3>
                        <ul className="list-disc pl-5 text-sm text-gray-700 font-sans">
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
                      <div>
                        <h3 className="font-semibold text-gray-800 mb-1 font-sans">Ceremony</h3>
                        <ul className="list-disc pl-5 text-sm text-gray-700 font-sans">
                          <li>Processional</li>
                          <li>Vows</li>
                          <li>Ring Exchange</li>
                          <li>First Kiss</li>
                          <li>Flowers to Mothers</li>
                          <li>Presentation of Couple</li>
                          <li>Recessional</li>
                        </ul>
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-800 mb-1 font-sans">Reception</h3>
                        <ul className="list-disc pl-5 text-sm text-gray-700 font-sans">
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

                  <p className="text-sm text-gray-600 mt-6 font-sans">
                    Essence does not recommend table shots. If you&apos;d like table shots, we require a second photographer. Please message us in the portal and we can help you.
                  </p>
                </section>

                <section className="p-6 bg-[#fdf4f5] rounded-lg border border-pinkbrand shadow-sm">
                  <h2 className="text-xl font-bold text-pinkbrand border-b border-pinkbrand pb-2 mb-4 font-display">
                    Family &amp; Wedding Party Info
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Left Column – Family Info */}
                    <div className="space-y-4">
                      <h3 className="font-semibold font-sans">Partner 1&apos;s Side</h3>
                      <label className="block text-sm font-medium text-gray-700 font-sans">P1&apos;s Parents:</label>
                      <input type="text" {...register("p1_parent_names")} className={inputClass} />

                      <label className="block text-sm font-medium text-gray-700 font-sans">P1&apos;s Siblings:</label>
                      <input type="text" {...register("p1_sibling_names")}  className={inputClass} />

                      <label className="block text-sm font-medium text-gray-700 font-sans">P1&apos;s Grandparents:</label>
                      <input type="text" {...register("p1_grandparent_names")} className={inputClass} />

                      <h3 className="font-semibold mt-6 font-sans">Partner 2&apos;s Side</h3>
                      <label className="block text-sm font-medium text-gray-700 font-sans">P2&apos;s Parents:</label>
                      <input type="text" {...register("p2_parent_names")} className={inputClass} />

                      <label className="block text-sm font-medium text-gray-700 font-sans">P2&apos;s Siblings:</label>
                      <input type="text" {...register("p2_sibling_names")} className={inputClass} />

                      <label className="block text-sm font-medium text-gray-700 font-sans">P2&apos;s Grandparents:</label>
                      <input type="text" {...register("p2_grandparent_names")} className={inputClass} />
                    </div>

                    {/* Right Column – Wedding Party Info */}
                    <div className="space-y-4">
                      <h3 className="font-semibold font-sans">Wedding Party</h3>
                      <label className="block text-sm font-medium text-gray-700 font-sans">Attendant of Honor P1:</label>
                      <input type="text" {...register("p1_attendant_of_honor")} className={inputClass} />

                      <label className="block text-sm font-medium text-gray-700 font-sans">Attendant of Honor P2:</label>
                      <input type="text" {...register("p2_attendant_of_honor")} className={inputClass} />

                      <label className="block text-sm font-medium text-gray-700 font-sans"># of Attendants P1:</label>
                      <input type="number" {...register("p1_attendant_qty")} className={inputClass} />

                      <label className="block text-sm font-medium text-gray-700 font-sans"># of Attendants P2:</label>
                      <input type="number" {...register("p2_attendant_qty")} className={inputClass} />

                      <label className="block text-sm font-medium text-gray-700 font-sans"># of Flower Attendants:</label>
                      <input type="number" {...register("flower_attendant_qty")} className={inputClass} />

                      <label className="block text-sm font-medium text-gray-700 font-sans"># of Ring Bearers:</label>
                      <input type="number" {...register("ring_bearer_qty")} className={inputClass} />

                      <label className="block text-sm font-medium text-gray-700 font-sans"># of Ushers:</label>
                      <input type="number" {...register("usher_qty")} className={inputClass}  />
                    </div>
                  </div>
                </section>

                {/* Additional Photography Requests Section */}
                <section className="p-6 bg-[#fdf4f5] rounded-lg border border-pinkbrand shadow-sm mb-10">
                  <h2 className="text-xl font-bold text-pinkbrand border-b border-pinkbrand pb-2 mb-4 font-display">
                    Additional Photography Requests
                  </h2>
                  <p className="mb-6 text-sm text-gray-700 font-sans">
                    Please add your photo requests below. We will do our best to get to all of them, time and weather permitting.
                  </p>

                  <div className="grid grid-cols-1 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Formal/Posed Photo Requests:</label>
                      <input
                        type="text"
                        {...register("additional_photo_request1")}
                        className={inputClass}
                      />

                      <label className="block text-sm font-medium text-gray-700">Formal/Posed Photo Requests (2):</label>
                      <input
                        type="text"
                        {...register("additional_photo_request2")}
                        className={inputClass}
                      />

                      <label className="block text-sm font-medium text-gray-700">Formal/Posed Photo Requests (3):</label>
                      <input
                        type="text"
                        {...register("additional_photo_request3")}
                        className={inputClass}
                      />

                      <label className="block text-sm font-medium text-gray-700">Other Photo Requests:</label>
                      <input
                        type="text"
                        {...register("additional_photo_request4")}
                        className={inputClass}
                      />

                      <label className="block text-sm font-medium text-gray-700">Other Photo Requests (2):</label>
                      <input
                        type="text"
                        {...register("additional_photo_request5")}
                        className={inputClass}
                      />
                    </div>
                  </div>
                </section>

                {/* Videography Customers Only Section */}
                <section className="p-6 bg-[#fdf4f5] rounded-lg border border-pinkbrand shadow-sm mb-10">
                  <h2 className="text-xl font-bold text-pinkbrand border-b border-pinkbrand pb-2 mb-4 font-display">
                    Videography Customers Only
                  </h2>
                  <p className="text-sm text-gray-700 mb-4 font-sans">
                    Essence cannot process your video until you have provided us with the following information.
                  </p>
                  <p className="text-sm text-gray-700 mb-4 font-sans">
                    Your final video will be delivered through Vimeo, the same cutting-edge platform trusted across the industry. We host it online for one year. Please be sure to download and save your video right away. After one year, the link will expire and be removed from our hosting. Feel free to store it wherever you like once you have it saved.
                  </p>
                  <p className="text-sm text-gray-700 mb-4 font-sans">
                    Please type your names below EXACTLY as you would like them to appear in the final video. Traditionally the names are listed as John and Sara Flemming.
                  </p>

                  <label htmlFor="video_client_names" className="block text-sm font-medium text-gray-700">Names:</label>
                  <input
                    id="video_client_names"
                    type="text"
                    {...register("video_client_names")}
                    className={inputClass}
                  />

                  <div className="mt-4 p-4 border-l-4 border-blue-400 bg-blue-50 rounded">
                    <p className="font-semibold mb-2">Notes:</p>
                    <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
                      <li>We arrive at least 1 hour before the ceremony to set up and capture essential highlight shots and set up sound for the ceremony.</li>
                      <li>Most packages include 8 hours of coverage.</li>
                      <li>Dance Highlight requires 2+ hours of open dancing.</li>
                      <li>Early starts (getting ready/first look) may mean no dance highlight if time runs out.</li>
                      <li><strong>Need more time?</strong> Overtime is available!</li>
                    </ul>
                  </div>

                  <p className="mt-4 text-sm font-sans">Questions? Message us anytime in the portal—we’re happy to help!</p>
                </section>

                {/* Wedding Story Section */}
                <section className="p-6 bg-[#fdf4f5] rounded-lg border border-pinkbrand shadow-sm">
                  <h2 className="text-xl font-bold text-pinkbrand border-b border-pinkbrand pb-2 mb-4 font-display">
                    Wedding Story
                  </h2>
                  <p className="text-sm text-gray-700 mb-2 font-sans">
                    Your wedding story will be a collection of highlights from your full wedding day. Your song selection should be one slow or medium tempo song. We strongly encourage you to pick a song with a length of 3–4 minutes, as a shorter song will decrease the amount of footage the editors are able to include in your highlight video. Re-edits of videos due to the choice of a short-length song will be charged a fee.
                  </p>

                  <label className="block text-sm font-medium text-gray-700 mt-4">WS Song Title:</label>
                  <input type="text" {...register("wedding_story_song_title")} className={inputClass} />

                  <label className="block text-sm font-medium text-gray-700 mt-4">WS Song Artist:</label>
                  <input type="text" {...register("wedding_story_song_artist")} className={inputClass} />
                </section>

                {/* Dance Montage Section */}
                <section className="p-6 bg-[#fdf4f5] rounded-lg border border-pinkbrand shadow-sm mt-6">
                  <h2 className="text-xl font-bold text-pinkbrand border-b border-pinkbrand pb-2 mb-4 font-display">
                    Dance Montage
                  </h2>
                  <p><strong className="text-red-600">Only if we’re there for 2 hours of open dancing.</strong></p>
                  <p className="text-sm text-gray-700 font-sans">
                    Your dance montage will be an upbeat collection of footage shot during the general dancing portion of your evening paired with one song. Re-edits of videos due to the choice of a short-length song will be charged a fee. We cannot complete your video without BOTH your Wedding Story and Dance Montage songs.
                  </p>

                  <label className="block text-sm font-medium text-gray-700 mt-4">DM Song Title:</label>
                  <input type="text" {...register("dance_montage_song_title")} className={inputClass} />

                  <label className="block text-sm font-medium text-gray-700 mt-4">DM Song Artist:</label>
                  <input type="text" {...register("dance_montage_song_artist")} className={inputClass} />
                </section>

                {/* Additional Editing Notes Section */}
                <section className="p-6 bg-[#fdf4f5] rounded-lg border border-pinkbrand shadow-sm mt-6">
                  <h2 className="text-xl font-bold text-pinkbrand border-b border-pinkbrand pb-2 mb-4 font-display">
                    Additional Editing Notes
                  </h2>
                  <p className="text-sm text-gray-700 mb-4 font-sans">
                    Videography customers receive the two above highlight videos as well as other important portions of their day. Customers who have not added Bridal Prep / First Look to their video coverage receive the following live footage: Ceremony, Introductions, Cake Cutting, Toasts, First Dance, Special Dances (i.e. Father/Daughter, Mother/Son), and Bouquet/Garter toss. These are only included if the events occur while the videographer is present.
                  </p>

                  <div className="mt-4 p-4 border-l-4 border-blue-400 bg-blue-50 rounded">
                    <p className="font-semibold mb-2">Additional Video Notes to Remember</p>
                    <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
                      <li>Videography customers receive one highlight video (their Wedding Story).</li>
                      <li>If we’re there for 2+ hours of open dancing late night, they’ll get a dance highlight included.</li>
                    </ul>
                  </div>
                </section>

                {/* Bridal Prep / First Look Section */}
                <section className="p-6 bg-[#fdf4f5] rounded-lg border border-pinkbrand shadow-sm mt-6">
                  <h2 className="text-xl font-bold text-pinkbrand border-b border-pinkbrand pb-2 mb-4 font-display">
                    Bridal Prep / First Look
                  </h2>
                  <p>Would be added to your Wedding Story (not a separate chapter).</p>
                  <p>Just remember: if you want early coverage, you may need to extend hours to ensure we’re there late for open dancing.</p>
                  <p className="mt-2">Other than our highlights, just a reminder of the specific chapters we showed you in your original meeting of our video:</p>
                  <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
                    <li>Ceremony</li>
                    <li>Introductions</li>
                    <li>Cake Cutting</li>
                    <li>Toasts</li>
                    <li>First Dance</li>
                    <li>Special Dances (e.g. Father/Daughter, Mother/Son)</li>
                    <li>Bouquet/Garter Toss</li>
                  </ul>
                  <p className="mt-2">These chapters are not edited—they are live.</p>
                  <p>If you have any other special dances or important moments, please list them below so we can make sure to include them and we’re aware of it.</p>
                </section>

                <label className="block text-sm font-medium text-gray-700 mt-4">Other Special Dances to be Included:</label>
                <input type="text" {...register("video_special_dances")} className={inputClass} />

                {/* Photo Booth Customers Only Section */}
                <section className="p-6 bg-[#fdf4f5] rounded-lg border border-pinkbrand shadow-sm mt-6">
                  <h2 className="text-xl font-bold text-pinkbrand border-b border-pinkbrand pb-2 mb-4 font-display">
                    Photo Booth Customers Only
                  </h2>
                  <p>Your open-air photo booth, with sparkly, silver backdrop and props, opens during the last 3 hours of the open dance time at your wedding. The booth prints (2) 2x6 photo strips for each set of images. The digital images will be sent to you as well, after the wedding via Google Drive. (Essence does not provide an album for photo strips.)</p>

                  <p className="mt-4">How would you like your names and wedding date to appear on your photo strip? (e.g., Kim and Joe, Joe & Kim, May 22, 2025, or 05/22/25)</p>

                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700">Text Line 1 (up to 15 characters):</label>
                    <input type="text" maxLength={15} {...register("photo_booth_text_line1")} className={inputClass} />
                  </div>

                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700">Text Line 2 (up to 15 characters):</label>
                    <input type="text" maxLength={15} {...register("photo_booth_text_line2")} className={inputClass} />
                  </div>

                  {/* New Field: Party End Time */}
                  <label className="block text-sm font-medium text-gray-700">What time does your party end?</label>
                  <StyledTimePicker
                    label="Photo Booth End Time"
                    value={photoBoothEndTimeRaw}
                    onChange={(val) => {
                      setPhotoBoothEndTimeRaw(val);
                      setValue("photo_booth_end_time", val, { shouldValidate: false });
                    }}
                  />
                  <input type="hidden" {...register("photo_booth_end_time")} />

                  <p className="text-sm text-gray-600 mt-1">We will do the last three hours of open dancing.</p>

                  <p className="mt-6">
                    Please describe the location in your facility where we will be setting up. Please remember that we will need a 5&#39;x7&#39; space within 15 feet of an outlet, and a skirted high-top table. (Example: You will be in the far corner of the room next to the head table, or you will be in the front, just inside the doors.)
                  </p>

                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700">Placement:</label>
                    <input type="text" {...register("photo_booth_placement")} className={inputClass} />
                  </div>
                </section>

                {/* Warning Message */}
                <div className="text-red-500 text-center mb-4">
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
            <div className="flex space-x-6 justify-center">
              {/* Save Button */}
              <button
                  type="button"
                  onClick={handleSave} // Save without validation
                  disabled={isSaving}
                  className="w-auto bg-[#fdf4f5] border-2 border-pinkbrand text-pinkbrand py-3 px-8 rounded-lg hover:bg-pinkbrand hover:text-white transition-all duration-300 transform hover:scale-105"
              >
                {isSaving ? 'Saving...' : 'Save'}
              </button>

              {/* Submit Button */}
              <button
                  type="submit"
                  disabled={isSubmitting || formSubmitted}
                  className="w-auto bg-[#fdf4f5] border-2 border-pinkbrand text-pinkbrand py-3 px-8 rounded-lg hover:bg-pinkbrand hover:text-white transition-all duration-300 transform hover:scale-105"
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