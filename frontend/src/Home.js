import React from 'react';
import logo from './logo.svg';
import axios from 'axios';
import './Home.css';

require('dotenv').config()


function Home() {
  function handleSubmit(event) {
    const text = document.querySelector('#type-input').value
    // Call to API on backend to get answer
    axios
      .get(`/get_items?type=${text}`).then(({data}) => {
        console.log(data)
        document.querySelector('#request').textContent = JSON.stringify(data)
      })
      .catch(err => console.log(err))
  }  
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.js</code> and save to reload.
        </p>
        <div>
        <label htmlFor='char-input'>Make an API Call</label>
        <input id='type-input' type='text' placeholder="items"/><span></span>
        <button onClick={handleSubmit}>have?</button>
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

export default Home;
