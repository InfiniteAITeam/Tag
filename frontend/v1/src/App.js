import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import TestFlow from "./pages/TestFlow";

export default function App(){return(<div className="app-shell">
  <Routes>
    <Route path="/" element={<Navigate to="/test" replace/>}/>
    <Route path="/test" element={<TestFlow demoMode={true} />} />

  </Routes></div>);}