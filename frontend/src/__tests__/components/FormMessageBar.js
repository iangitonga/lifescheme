import {render} from "@testing-library/react";
import React from "react";
import FormMessageBar from "../../components/FormMessageBar";


test('renders without crashing.', () => {
    render(<FormMessageBar/>);
});
