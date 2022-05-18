import React, { useState } from 'react';
import logo from './static/construction.png';
import axios from 'axios';
import './Home.css';

// will house items, short summary and all other information made available via the MongoDB instance

function Constuction() {
  
    return (
      <div className="App">
        <header className="App-header">
          <img src={logo} className="Construction-logo"></img>
          <b>This page is currently under construction. Check back soon for more features!</b>
        </header>
      </div>
    );
  }
  
  export default Constuction;
  