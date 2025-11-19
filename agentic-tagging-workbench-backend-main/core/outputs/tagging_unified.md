# Tagging Suggestions Report

- **Excel**: `/home/sgadal/ATTagger/AI_Tagging_Sys/core/techSpecAgent/TechSpecOutputs/techspec.xlsx`
- **Repo**: `/home/sgadal/ATTagger/Test/ResidentPortal`
- **Items**: 6

## Page: AutoPay
### KPI: Resident enters lease ID for AutoPay and taps CONTINUE
- **Action**: `click`
- **Adobe**: var=`eVar27`, value=`Continue_AutoPay_leaseId`
- **Suggested Location**: `/home/sgadal/ATTagger/Test/ResidentPortal/src/pages/EnterNumber.js:17`  (confidence 0.86)
- **Why here**: The button for CONTINUE is located in the EnterNumber.js file, which handles the user input for AutoPay.
- **Event**: `AutoPay_Continue_Click`
- **Params:**
```json
{
  "eVar27": "Continue_AutoPay_leaseId",
  "events": "event1",
  "__pv": false,
  "pageName": "AutoPay"
}
```
- **Implementation**: Track the click event on the CONTINUE button to capture the lease ID entry.
- **Risks**: Button may not be clicked if validation fails, User may not enter a valid lease ID

```jsx
  11:     <h1 className="hero">Enter your lease ID or unit number for {paymentOption.toLowerCase()} payment.</h1>
  12:     <form className="entry" onSubmit={onSubmit}>
  13:       <label className="field"><span className="label">{paymentOption}, Lease ID or unit number</span>
  14:         <input type="text" inputMode="numeric" pattern="\d*" value={value} onChange={(e)=>setValue(e.target.value.replace(/\D/g,'').slice(0,maxLen))}/>
  15:       </label>
  16:       <Keypad onPress={onKey}/>
  17:       <button type="submit" className="btn primary" disabled={value.length<Math.min(6,maxLen)}>Continue</button>
  18:     </form></div></div>);
  19: }
```

**Suggested code to add:**

_Imports (add once per file if missing):_
```js
import { track } from '../analytics/track.js';
```

_Hook (page view):_
```jsx
useEffect(() => { return () => { /* cleanup if necessary */ }; }, []);
```

_JSX attributes (apply to the element):_
```jsx
<YourElement
onClick={() => track('AutoPay_Continue_Click', { eVar27: 'Continue_AutoPay_leaseId' })}
>
  ...
</YourElement>
```

_Alternative wrapper (if preserving existing handler):_
```js
onClick={handleClick}
```
## Page: Monthly Lease
### KPI: Resident enters lease ID for Monthly and taps CONTINUE
- **Action**: `submit`
- **Adobe**: var=`eVar27`, value=`Continue_Monthly_leaseId`
- **Suggested Location**: `/home/sgadal/ATTagger/Test/ResidentPortal/src/pages/EnterNumber.js:17`  (confidence 0.86)
- **Why here**: The submit button for the form is where the user interacts to submit the lease ID.
- **Event**: `submit_lease_id`
- **Params:**
```json
{
  "eVar27": "Continue_Monthly_leaseId",
  "events": "event1",
  "pageName": "Monthly Lease"
}
```
- **Implementation**: Track the submission of the lease ID when the CONTINUE button is clicked.
- **Risks**: User may not enter a valid lease ID, Form submission may fail

```jsx
  11:     <h1 className="hero">Enter your lease ID or unit number for {paymentOption.toLowerCase()} payment.</h1>
  12:     <form className="entry" onSubmit={onSubmit}>
  13:       <label className="field"><span className="label">{paymentOption}, Lease ID or unit number</span>
  14:         <input type="text" inputMode="numeric" pattern="\d*" value={value} onChange={(e)=>setValue(e.target.value.replace(/\D/g,'').slice(0,maxLen))}/>
  15:       </label>
  16:       <Keypad onPress={onKey}/>
  17:       <button type="submit" className="btn primary" disabled={value.length<Math.min(6,maxLen)}>Continue</button>
  18:     </form></div></div>);
  19: }
```

**Suggested code to add:**

_Imports (add once per file if missing):_
```js
import { track } from '../analytics/track.js';
```

_JSX attributes (apply to the element):_
```jsx
<YourElement
onClick={() => track('submit_lease_id', { eVar27: 'Continue_Monthly_leaseId', events: 'event1' })}
>
  ...
</YourElement>
```

_Alternative wrapper (if preserving existing handler):_
```js
onSubmit={(e) => { e.preventDefault(); track('submit_lease_id', { eVar27: 'Continue_Monthly_leaseId', events: 'event1' }); }}
```
## Page: Payment Options
### KPI: Resident selects Monthly payment option
- **Action**: `select`
- **Adobe**: var=`eVar27`, value=`Select_PaymentOption_Monthly`
- **Suggested Location**: `/home/sgadal/ATTagger/Test/ResidentPortal/src/pages/PaymentOption.js:7`  (confidence 0.86)
- **Why here**: The event handler for selecting the payment option is located in the PaymentOption component.
- **Event**: `select_payment_option`
- **Params:**
```json
{
  "eVar27": "Select_PaymentOption_Monthly",
  "pageName": "Payment Options"
}
```
- **Implementation**: Track the selection of the Monthly payment option when the corresponding tile is clicked.
- **Risks**: Incorrect event tracking if the handler is not properly set up, Potential performance issues if tracking is not optimized

```jsx
   1: import React from 'react';
   2: import { useNavigate } from 'react-router-dom';
   3: export default function PaymentOption(){
   4:   const nav=useNavigate();
   5:   const pick=(type)=>nav('/enter-number',{state:{paymentOption:type}});
   6:   return(<div className="screen"><div className="page">
   7:     <div className="toolbar"><button className="link" onClick={()=>nav(-1)}>← Back</button><div className="spacer"/><button className="link" onClick={()=>nav('/help')}>Exit</button></div>
   8:     <h1 className="hero">Select your rent payment option</h1>
   9:     <div className="grid-2 compact">
  10:       <div className="tile big" onClick={()=>pick('Monthly')}><span>Monthly payment</span></div>
  11:       <div className="tile big" onClick={()=>pick('AutoPay')}><span>Set up AutoPay</span></div>
  12:     </div></div></div>);
  13: }
```

**Suggested code to add:**

_Imports (add once per file if missing):_
```js
import { track } from '../analytics/track.js';
```

_JSX attributes (apply to the element):_
```jsx
<YourElement
onClick={() => { track('select_payment_option', { eVar27: 'Select_PaymentOption_Monthly' }); pick('Monthly'); }}
>
  ...
</YourElement>
```
### KPI: Resident selects Set up AutoPay option
- **Action**: `select`
- **Adobe**: var=`eVar27`, value=`Select_PaymentOption_AutoPay`
- **Suggested Location**: `/home/sgadal/ATTagger/Test/ResidentPortal/src/pages/PaymentOption.js:11`  (confidence 0.86)
- **Why here**: The event handler for selecting the AutoPay option is located in the PaymentOption.js file, specifically on line 11 where the clickable element is defined.
- **Event**: `select_payment_option`
- **Params:**
```json
{
  "eVar27": "Select_PaymentOption_AutoPay",
  "events": "event1",
  "__pv": false,
  "pageName": "Payment Options"
}
```
- **Implementation**: Ensure that the track function is called within the onClick handler for the AutoPay option.
- **Risks**: Event may not fire if the handler is not correctly implemented, Potential for duplicate events if not properly managed

```jsx
   5:   const pick=(type)=>nav('/enter-number',{state:{paymentOption:type}});
   6:   return(<div className="screen"><div className="page">
   7:     <div className="toolbar"><button className="link" onClick={()=>nav(-1)}>← Back</button><div className="spacer"/><button className="link" onClick={()=>nav('/help')}>Exit</button></div>
   8:     <h1 className="hero">Select your rent payment option</h1>
   9:     <div className="grid-2 compact">
  10:       <div className="tile big" onClick={()=>pick('Monthly')}><span>Monthly payment</span></div>
  11:       <div className="tile big" onClick={()=>pick('AutoPay')}><span>Set up AutoPay</span></div>
  12:     </div></div></div>);
  13: }
```

**Suggested code to add:**

_Imports (add once per file if missing):_
```js
import { track } from '../analytics/track.js';
```

_JSX attributes (apply to the element):_
```jsx
<YourElement
onClick={() => { track('select_payment_option', { eVar27: 'Select_PaymentOption_AutoPay', events: 'event1' }); pick('AutoPay'); }}
>
  ...
</YourElement>
```
## Page: Rent Payment
### KPI: Resident selects 'Make a rent Payment'
- **Action**: `select`
- **Adobe**: var=`eVar27`, value=`Select_MakeARentPayment`
- **Suggested Location**: `/home/sgadal/ATTagger/Test/ResidentPortal/src/pages/Help.js:9`  (confidence 0.85)
- **Why here**: The event handler for the clickable element is located here.
- **Event**: `selectMakeARentPayment`
- **Params:**
```json
{
  "eVar27": "Select_MakeARentPayment",
  "__pv": false,
  "pageName": "Rent Payment"
}
```
- **Implementation**: Ensure the track function is called within the onClick handler.
- **Risks**: Event may not fire if the handler is not correctly set up., Potential for duplicate events if not managed properly.

```jsx
   3: export default function Help(){
   4:   const nav=useNavigate();
   5:   return(<div className="screen"><div className="page">
   6:     <div className="toolbar"><div className="pill">Today ▾</div><div className="spacer"/><a className="link ghost" href="#">Español</a><a className="link ghost" href="#">Reviews</a></div>
   7:     <h1 className="hero red">What can we help you with today?</h1>
   8:     <div className="grid-2">
   9:       <div className="card action" onClick={()=>nav('/payment-Option')}><h3>Make a rent Payment</h3><p>Make a one-time payment or set up auto pay.</p><div className="chev">→</div></div>
  10:       <div className="card"><h3>Start a new application</h3><p>Apply for a unit in minutes.</p><div className="chev">→</div></div>
  11:       <div className="card"><h3>Request maintenance</h3><p>Report repairs or issues.</p><div className="chev">→</div></div>
  12:       <div className="card ghost"><h3>More options</h3><p>Documents, FAQs, and more.</p></div>
  13:     </div></div></div>);
  14: }
```

**Suggested code to add:**

_Imports (add once per file if missing):_
```js
import { track } from '../analytics/track.js';
```

_JSX attributes (apply to the element):_
```jsx
<YourElement
onClick={() => { track('selectMakeARentPayment', { eVar27: 'Select_MakeARentPayment' }); nav('/payment-Option'); }}
>
  ...
</YourElement>
```
## Page: Reporting Requirement
### KPI: Resident taps the BACK button
- **Action**: `back`
- **Adobe**: var=`eVar27`, value=`Back`
- **Suggested Location**: `/home/sgadal/ATTagger/Test/ResidentPortal/src/pages/EnterNumber.js:10`  (confidence 0.85)
- **Why here**: The BACK button is a clickable JSX element that triggers navigation.
- **Event**: `backButtonClick`
- **Params:**
```json
{
  "eVar27": "Back",
  "events": "event1",
  "__pv": false,
  "pageName": "Reporting Requirement"
}
```
- **Implementation**: Track the BACK button click event to capture user navigation behavior.
- **Risks**: Event may not fire if navigation fails, User may not expect tracking on BACK button

```jsx
   4: export default function EnterNumber(){
   5:   const nav=useNavigate(); const {state}=useLocation(); const paymentOption=state?.paymentOption||'Monthly';
   6:   const [value,setValue]=useState(''); const maxLen=paymentOption==='Monthly'?10:12;
   7:   const onKey=(k)=>{ if(k==='Clear') return setValue(''); if(k==='⌫') return setValue(v=>v.slice(0,-1)); if(/^\d$/.test(k)) setValue(v=>(v+k).slice(0,maxLen)); };
   8:   const onSubmit=(e)=>{ e.preventDefault(); if(value.length<Math.min(6,maxLen)) return; alert(`Mock submit for ${paymentOption}: ${value}`); };
   9:   return(<div className="screen"><div className="page">
  10:     <div className="toolbar"><button className="link" onClick={()=>nav(-1)}>← Back</button><div className="spacer"/><button className="link" onClick={()=>nav('/help')}>Exit</button></div>
  11:     <h1 className="hero">Enter your lease ID or unit number for {paymentOption.toLowerCase()} payment.</h1>
  12:     <form className="entry" onSubmit={onSubmit}>
  13:       <label className="field"><span className="label">{paymentOption}, Lease ID or unit number</span>
  14:         <input type="text" inputMode="numeric" pattern="\d*" value={value} onChange={(e)=>setValue(e.target.value.replace(/\D/g,'').slice(0,maxLen))}/>
  15:       </label>
  16:       <Keypad onPress={onKey}/>
```

**Suggested code to add:**

_Imports (add once per file if missing):_
```js
import { track } from '../analytics/track.js';
```

_JSX attributes (apply to the element):_
```jsx
<YourElement
onClick={() => { track('backButtonClick', { eVar27: 'Back', events: 'event1' }); nav(-1); }}
>
  ...
</YourElement>
```

---

## Optional analytics helper
_Create `src/analytics/track.js` if you don't already have a tracking util:_
```js
// src/analytics/track.js
export function track(eventName, params = {}) {
  const s = window && window.s;
  if (!s) {
    // eslint-disable-next-line no-console
    console.warn('[track] Adobe AppMeasurement `s` not found. Event:', eventName, params);
    return;
  }
  const isPageView = !!params.__pv;
  const { __pv, events, ...rest } = params;
  const prevLinkTrackVars = s.linkTrackVars;
  const prevLinkTrackEvents = s.linkTrackEvents;
  try {
    const varNames = [];
    for (const [k, v] of Object.entries(rest)) {
      if (/^(eVar|prop)\d+$/i.test(k)) { s[k] = v; varNames.push(k); }
      else if (k === 'pageName') { s.pageName = v; varNames.push('pageName'); }
    }
    if (isPageView) {
      if (events) s.events = events; // e.g., 'event10'
      s.t();               // page view call
      s.clearVars();       // prevent bleed to next hit
      return;
    }
    // Link tracking (CTA/click)
    s.linkTrackVars = varNames.concat('events').join(',');
    if (events) s.linkTrackEvents = events;
    s.events = events || '';
    s.tl(true, 'o', eventName);  // 'o' = custom link, name = eventName
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error('track error', e);
  } finally {
    s.linkTrackVars = prevLinkTrackVars;
    s.linkTrackEvents = prevLinkTrackEvents;
  }
}
```