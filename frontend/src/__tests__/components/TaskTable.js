import {render} from "@testing-library/react";
import React from "react";
import TaskTable from "../../components/TaskTable";


test('renders without crashing.', () => {
    render(<TaskTable/>);
});