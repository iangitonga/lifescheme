import React from "react";
import ReactDOM from 'react-dom';
import TaskTableRow from "../../components/TaskTableRow";


test('renders without crashing.', () => {
    // Unlike other tests, here, we use `ReactDom.render` TO ensure that table
    // row is rendered under tbody element parent.
    const table = document.createElement('tbody');
    ReactDOM.render(<TaskTableRow/>, table);
});