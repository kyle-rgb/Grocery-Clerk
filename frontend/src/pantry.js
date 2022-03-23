import React, { useState } from 'react';
import logo from './logo.svg';
import axios from 'axios';
import './Home.css';

// will house items, short summary and all other information made available via the MongoDB instance

function Pantry() {
  
    return (
      <div className="App">
        <header className="App-header">
          <p>
            <code>My Swanky New Page</code>
          </p>
          <div>
            <label htmlFor='char-input'>Make an API Call</label>
            <input id='type-input' type='text' placeholder="items"/><span></span>
            <button >have?</button>
          <div>
            <h3>Return values: </h3>
            <br />
            <code id='request' data-testid="get_items"></code>
          </div>
        </div>
        </header>
      </div>
    );
  }
  
  export default Pantry;
  