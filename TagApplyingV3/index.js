import { store } from 'onevzsoemfeframework/Storemfe';
import basicDlObject from './dlStructure';
import { getPaymentTypeLabel } from '../util/getBillPayment';

// Custom hook for tagging
const useTagging = () => {
  // Use useRef to persist data across renders without causing reloads
  // Helper to build defaultDL only when needed
  const buildDefaultDL = (type = '', flow = '', isFlowNameUpdate = false) => {
    const state = store.getState();
    const peripheralsInfo = state?.peripheralsInfo?.appInitVars || {};
    const userInfo = state?.billPay?.userData || {};
    const scanInfo = state?.scan?.repLoginData?.data || {};
    const commonDetails = state?.common || {};
    const billType = state?.billPay?.billType || '';
    const prepaidData = state?.billPay?.prePaidData || {};
    const billData = state?.billPay?.billSummary || {};
    const adaptiveData = state.common?.adaptiveLoginData;
    const paymentData = commonDetails?.paymentData || {};

    const defaultDL =
      typeof structuredClone === 'function'
        ? structuredClone(basicDlObject)
        : JSON.parse(JSON.stringify(basicDlObject));

    // Helper functions for each section
    const setUserInfo = () => {
      if (!userInfo?.mtn && !userInfo?.isFiosFlow) return;
      const accountParts = userInfo?.accountNumber?.split('-') || [];
      defaultDL.user.accountLast2 = accountParts[0]?.slice(-2) || '';
      defaultDL.user.acctId_unhashed = userInfo.accountNumber || '';

      if (userInfo?.isFiosFlow) {
        defaultDL.user.accountType = userInfo?.prepayAccount ? 'Prepay' : 'Postpay';
        defaultDL.user.authType = 'logged in';
        defaultDL.user.custId_unhashed = '';
      } else {
        defaultDL.user.accountType = userInfo?.accountType ?? '';
        defaultDL.user.custId_unhashed = accountParts[0] || '';
        defaultDL.user.id = billData?.mtnHashCode || '';
        defaultDL.user.account = billData?.accountHashCode || '';
      }

      if (userInfo?.verifiedBy) {
        defaultDL.user.authStatus = userInfo.verifiedBy === 'BLINDPAY' ? 'anonymous' : 'logged in';
        if (userInfo.verifiedBy === 'MY_VERIZON') {
          defaultDL.user.authType = adaptiveData?.listOfDevices?.[0]?.deviceType === 'BASIC' ? 'sms' : 'push';
        } else if (userInfo.verifiedBy === 'ACCOUNT_PIN') {
          defaultDL.user.authType = 'pin';
        }
      }
    };

    const setScanInfo = () => {
      if (!Object.keys(scanInfo).length) return;
      defaultDL.txn.agent = scanInfo.salesRepId ?? '';
      defaultDL.txn.agentRole = scanInfo.details?.jobTitledId ?? '';
    };

    const setCustomerInfo = () => {
      if (!Object.keys(userInfo).length) return;
      defaultDL.user.customerType = userInfo.customerType ?? '';
      defaultDL.user.customerRole = userInfo.amRole ?? '';
    };

    const setPrepaidInfo = () => {
      if (!Object.keys(prepaidData).length) return;
      defaultDL.user.id = prepaidData.hashed_mdn ?? '';
    };

    const setPaymentInfo = () => {
      if (!Object.keys(paymentData).length) return;
      if (paymentData.orderTotal) {
        defaultDL.txn.paymentAmt = Number(paymentData.orderTotal);
        defaultDL.txn.total = paymentData.orderTotal;
        defaultDL.txn.taxAmt = prepaidData?.taxInfo?.total_fee_amount ?? '';
      }
      if (paymentData?.paymentType) {
        defaultDL.txn.paymentType = getPaymentTypeLabel(paymentData.paymentType);
      }
      if (billType) {
        defaultDL.env.businessUnit = billType === 'mobile' ? 'Wireless' : 'Wireline';
      }
      defaultDL.txn.id =
        paymentData?.order_number ||
        paymentData?.orderNumber ||
        paymentData?.orderNum ||
        paymentData?.responseDetail?.pmtConfirmationNumber ||
        paymentData?.orders?.[0]?.orderNum ||
        defaultDL.txn.id;
    };

    const setPageLoadInfo = () => {
      if (type !== 'trackPageLoad') return;
      const machineType = peripheralsInfo.isPaypodEnabled ? 'paypod' : 'kiosk';
      const machineName = peripheralsInfo.machineName ?? '';
      const registerNumber = peripheralsInfo.registerNumber ?? '';
      defaultDL.page.formData = `bpkMachReg^|t:${machineType}|m:${machineName}|r:${registerNumber} |`;
    };

    const setFlowName = () => {
      if (type !== 'trackPageLoad' || !isFlowNameUpdate) return;
      const isFiosFlow = !!userInfo?.isFiosFlow;
      const menu = commonDetails?.menuSelected;
      if (menu === 'payBill') {
        defaultDL.page.flow = `${isFiosFlow ? 'pay bill home internet' : 'pay bill mobile'}-${flow}`;
      } else if (menu === 'completeOrder') {
        defaultDL.page.flow = `Complete order-${flow}`;
      } else {
        defaultDL.page.flow = `Scan And Go-${flow}`;
      }
    };

    // Call helpers
    setUserInfo();
    setScanInfo();
    setCustomerInfo();
    setPrepaidInfo();
    setPaymentInfo();
    setPageLoadInfo();
    setFlowName();

    // Set outletId always
    defaultDL.txn.outletId = peripheralsInfo.locationCode ?? '';
    defaultDL.page.channelSession = localStorage.getItem('bpkUUID') ?? '';

    return defaultDL;
  };

  const trackPageLoad = ({ pageName = '', flow = '', subFlow = '', event = '', isFlowNameUpdate = false } = {}) => {
    try {
      const model = buildDefaultDL('trackPageLoad', flow, isFlowNameUpdate);
      model.page.name = pageName;
      if (!isFlowNameUpdate) {
        model.page.flow = flow;
      }
      model.page.subFlow = subFlow;
      model.event.value = event;
      window.vzdl = model;
      window.coreData = window.coreData ?? [];
      window.coreData.push({
        task: 'emit',
        event: 'pageView',
      });
    } catch (e) {
      console.error('Error in site catalyst ', e);
    }
  };

  const trackPageNotification = (name = '', message = '', id = '') => {
    try {
      const data = buildDefaultDL();
      window.vzdl = data;
      window.coreData = window.coreData ?? [];
      window.coreData.push({
        task: 'emit',
        event: 'notify',
        params: {
          name,
          message,
          error: true,
          id,
        },
      });
    } catch (e) {
      console.log('Error in site catalyst', e);
    }
  };

  const trackPageChange = (selectorIdOrClass = '', message = '') => {
    try {
      const data = buildDefaultDL();
      window.vzdl = data;
      window.coreData.push({
        task: 'emit',
        event: 'openView',
        params: {
          selector: selectorIdOrClass,
          message,
        },
      });
    } catch (e) {
      console.log('Error in site catalyst', e);
    }
  };

  return { trackPageLoad, trackPageNotification, trackPageChange };
};

export { useTagging };
