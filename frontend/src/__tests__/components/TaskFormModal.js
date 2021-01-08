import {render} from "@testing-library/react";
import React from "react";
import TaskFormModal from "../../components/TaskFormModal";


test('renders without crashing.', () => {
    render(<TaskFormModal/>);
});