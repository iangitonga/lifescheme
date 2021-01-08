import {render} from "@testing-library/react";
import React from "react";
import TaskForm from "../../components/TaskForm";


test('renders without crashing.', () => {
    render(<TaskForm/>);
});