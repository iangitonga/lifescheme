import {render} from "@testing-library/react";
import React from "react";
import TaskStatusCheckbox from "../../components/TaskStatusCheckbox";


test('renders without crashing.', () => {
    render(<TaskStatusCheckbox/>);
});