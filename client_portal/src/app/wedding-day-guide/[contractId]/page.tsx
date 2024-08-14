'use client'; // Mark this as a Client Component

import { useParams } from 'next/navigation';
import WeddingDayGuideForm from '../../../../client_***REMOVED***m';
import styles from '../../../../client_portal/src/components/WeddingDayGuide.module.css';

const WeddingDayGuidePage = () => {
  const params = useParams();
  const contractId = params.contractId;

  // Handle the case where contractId could be an array or undefined
  const resolvedContractId = Array.isArray(contractId) ? contractId[0] : contractId;

  if (!resolvedContractId) {
    return <p>Loading...</p>;
  }

  return (
    <div className={styles.container}>
      <h1 className={styles.heading}>Wedding Day Guide Form</h1>
      <WeddingDayGuideForm contractId={resolvedContractId} />
    </div>
  );
};

export default WeddingDayGuidePage;
