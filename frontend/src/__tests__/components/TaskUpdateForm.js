import {render} from "@testing-library/react";
import React from "react";
import TaskUpdateForm from "../../components/TaskUpdateForm";


test('renders without crashing.', () => {
    render(<TaskUpdateForm/>);
});