import React from 'react';
import './App.css';
import Navbar from './components/Navbar';
import { Tabs, Tab } from 'react-bootstrap';
import ExoplanetsTab from './components/ExoplanetsTab';
import MarsTab from './components/MarsTab';
import IssTab from './components/IssTab';

function App() {
  return (
    <>
      <Navbar />
      <div className="container mt-4">
        <Tabs defaultActiveKey="exoplanets" id="space-data-tabs" className="mb-3">
          <Tab eventKey="exoplanets" title="Exoplanets">
            <ExoplanetsTab />
          </Tab>
          <Tab eventKey="mars" title="Mars">
            <MarsTab />
          </Tab>
          <Tab eventKey="iss" title="ISS">
            <IssTab />
          </Tab>
        </Tabs>
      </div>
    </>
  );
}

export default App;
