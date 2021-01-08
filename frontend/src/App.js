import React, {Fragment} from 'react';
import './App.css';
import TaskTable from "./components/TaskTable";


function App() {
  return (
    <Fragment>
        {/*<div className="main-container">*/}
            <TaskTable/>
        {/*</div>*/}
    </Fragment>
  );
}

export default App;
