'use client'; // Mark this as a Client Component

import { useParams } from 'next/navigation';
import WeddingDayGuideForm from '../../../components/WeddingDayGuideForm';
import styles from '../../../components/WeddingDayGuide.module.css';

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
      <WeddingDayGuideForm contractId={resolvedContractId} />
    </div>
  );
};

export default WeddingDayGuidePage;
