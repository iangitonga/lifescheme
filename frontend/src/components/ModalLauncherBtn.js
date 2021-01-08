import React from "react";


export default class ModalLauncherBtn extends React.Component {
    render() {
        return <button className='btn' onClick={this.props.clickCbc}>Create new task</button>;
    }
}
