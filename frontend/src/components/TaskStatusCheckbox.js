import React from "react";


export default class TaskStatusCheckbox extends React.Component {
    constructor(props) {
        super(props);
        this.uncheckedP = 'M5 2c-1.654 0-3 1.346-3 3v14c0 1.654 1.346 3 3 3h14c1.654 0 3-1.346 3-3v-14c0-1.654-1.346-3-3-3h-14zm19 3v14c0 2.761-2.238 5-5 5h-14c-2.762 0-5-2.239-5-5v-14c0-2.761 2.238-5 5-5h14c2.762 0 5 2.239 5 5z';
        this.checkedP = 'M19 0h-14c-2.762 0-5 2.239-5 5v14c0 2.761 2.238 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-8.959 17l-4.5-4.319 1.395-1.435 3.08 2.937 7.021-7.183 1.422 1.409-8.418 8.591z';
    }

    render() {
        return (
            <button
                className="task-status-link"
                type="submit"
                onClick={this.props.taskStatusUpdateCbc}>
                <svg xmlns="http://www.w3.org/2000/svg"
                    className={`task-status-link__checkbox-svg ${this.props.checked ? 'task-status-link__checkbox-svg--checked' : ''}`}
                     width="20" height="22" viewBox="0 0 24 24">
                    <path d={this.props.checked ? this.checkedP : this.uncheckedP}/>
                </svg>
            </button>
        );
    }
}
