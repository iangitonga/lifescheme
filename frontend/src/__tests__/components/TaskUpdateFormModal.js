import {render} from "@testing-library/react";
import React from "react";
import TaskUpdateFormModal from "../../components/TaskUpdateFormModal";


test('renders without crashing.', () => {
    render(<TaskUpdateFormModal/>);
});