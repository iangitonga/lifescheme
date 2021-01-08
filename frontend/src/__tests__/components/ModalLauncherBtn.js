import {render} from "@testing-library/react";
import React from "react";
import ModalLauncherBtn from "../../components/ModalLauncherBtn";


test('renders without crashing.', () => {
    render(<ModalLauncherBtn/>);
});
