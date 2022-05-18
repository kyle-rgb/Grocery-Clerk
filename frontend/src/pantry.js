import React, { useState } from 'react';
import logo from './static/construction.png';
import axios from 'axios';
import './Home.css';

// will house items, short summary and all other information made available via the MongoDB instance

function Pantry() {
  
    return (
      <div className="App">
        <header className="App-header">
          <p>
            1.) Pantry: <code>A Catalouge of longer shelf life, dry good items in stock @ home.</code>
            <br />
            2.) Fridge/Freezer: <code>A Catalouge of shorter shelf life, temperature controlled goods @ home.</code>
          </p>
          
        </header>
      </div>
    );
  }
  
  export default Pantry;
  